from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models.functions import Concat, Substr
from django.utils import timezone
from uuid_extensions import uuid7

from djangopress.spaces.models import Space

from . import paths


__all__ = ["PageContentType", "Page", "PageRevision", "PageStatus"]


class PageContentType(models.Model):
    space = models.ForeignKey(
        Space, on_delete=models.CASCADE, related_name="page_content_types"
    )
    name = models.TextField()
    version = models.PositiveIntegerField(default=1)
    schema = models.JSONField()

    # Fields for migrating to next content type
    # When a new version of the content type is created,
    # or this content type is merged into another,
    # the migration_target is set to the content type
    # all instances of this type will be converted to and
    # migration_operations is set to a list of operations
    # to convert content of this type to the target type.
    migration_target = models.ForeignKey(
        "self", on_delete=models.SET_NULL, null=True, blank=True, related_name="+"
    )
    migration_operations = models.JSONField(null=True, blank=True)

    class Meta:
        db_table = "djangopress_pagecontenttype"
        unique_together = [("space", "name", "version")]
        ordering = ["name"]

    def __str__(self):
        return self.name

    def get_form_class(self, include_slug=False):
        """
        Builds a Django Form class from this content type's schema.

        See ``djangopress.pages.schema`` --- this is the heart of the CMS.
        """
        from .schema import build_form_class

        return build_form_class(self, include_slug=include_slug)

    @property
    def field_count(self):
        return len(self.schema.get("fields", []))


class PageStatus(models.TextChoices):
    DRAFT = "draft", "Draft"
    LIVE = "live", "Live"
    LIVE_PLUS_DRAFT = "live+draft", "Live + draft"
    UNPUBLISHED = "unpublished", "Unpublished"


class PageQuerySet(models.QuerySet):
    """
    Tree queries, all of them expressed against ``path`` and ``path_depth``.

    See ``djangopress.pages.paths`` for why paths always carry a trailing
    slash --- the prefix matching below depends on it.
    """

    def children_of(self, path):
        path = paths.normalise(path)
        return self.filter(
            path__startswith=path, path_depth=paths.depth(path) + 1
        )

    def descendants_of(self, path, inclusive=False):
        path = paths.normalise(path)
        queryset = self.filter(path__startswith=path)
        return queryset if inclusive else queryset.exclude(path=path)

    def ancestors_of(self, path, inclusive=False):
        # No prefix scan and no recursion: the ancestor paths are derivable
        # from the path string, so this is a single indexed IN lookup.
        return self.filter(path__in=paths.ancestors_of(path, inclusive=inclusive))

    def siblings_of(self, path, inclusive=False):
        parent_path = paths.parent_of(path)
        if parent_path is None:
            return self.none()

        queryset = self.children_of(parent_path)
        return queryset if inclusive else queryset.exclude(path=paths.normalise(path))


class Page(models.Model):
    """
    A page.

    ``content`` always holds the *draft* (the working copy). What the public
    site serves is ``live_revision.content``. Keeping those separate means
    "save draft" and "publish" are two plainly different operations rather
    than a stack of flags, which makes the view code much easier to read.
    """

    id = models.UUIDField(primary_key=True, default=uuid7)
    space = models.ForeignKey(Space, on_delete=models.CASCADE, related_name="pages")

    # The full URL path within the space, with a leading and trailing slash.
    # This is the page's identity: serving a request is one exact-match lookup.
    path = models.TextField()
    # Number of segments in `path`. Denormalised so that "children of X" is an
    # indexed prefix scan plus an equality check rather than a LIKE that has to
    # count slashes.
    path_depth = models.PositiveIntegerField(default=0)
    slug = models.SlugField(max_length=255, default="")

    content_type = models.ForeignKey(
        PageContentType, on_delete=models.CASCADE, related_name="pages"
    )
    content = models.JSONField()
    title = models.TextField()

    # Publishing
    live = models.BooleanField(default=False)
    has_unpublished_changes = models.BooleanField(default=False)
    live_revision = models.ForeignKey(
        "PageRevision",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
    )
    latest_revision = models.ForeignKey(
        "PageRevision",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
    )
    first_published_at = models.DateTimeField(null=True, blank=True)
    last_published_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = PageQuerySet.as_manager()

    class Meta:
        db_table = "djangopress_page"
        unique_together = [("space", "path")]
        # Manual sibling ordering is deliberately not supported --- with paths
        # as identity there's nowhere to hang it. Children come back in path
        # order, which means the listing and the site agree.
        ordering = ["path"]
        indexes = [
            models.Index(fields=["space", "path_depth"]),
        ]
        # NOTE: on PostgreSQL, `path__startswith` compiles to LIKE 'x%', which
        # a plain B-tree index won't serve under a non-C collation. If the
        # descendant queries ever get hot, add:
        #   CREATE INDEX ... ON djangopress_page (path text_pattern_ops);
        # The exact-match routing lookup is already covered by the unique
        # constraint on (space, path).

    def __str__(self):
        return self.title

    # -- Tree --------------------------------------------------------------

    def get_parent(self):
        parent_path = paths.parent_of(self.path)
        if parent_path is None:
            return None
        return Page.objects.filter(space=self.space, path=parent_path).first()

    def get_children(self):
        return Page.objects.filter(space=self.space).children_of(self.path)

    def get_descendants(self, inclusive=False):
        return Page.objects.filter(space=self.space).descendants_of(
            self.path, inclusive=inclusive
        )

    def get_ancestors(self, inclusive=False):
        return Page.objects.filter(space=self.space).ancestors_of(
            self.path, inclusive=inclusive
        )

    def get_siblings(self, inclusive=False):
        return Page.objects.filter(space=self.space).siblings_of(
            self.path, inclusive=inclusive
        )

    def place_under(self, parent_path, slug=None):
        """
        Set this page's slug, path and depth from a parent path.

        Does not touch descendants --- use :meth:`move_to` for that.
        """
        parent_path = paths.normalise(parent_path)
        slug = slug or self.slug or paths.suggest_slug(self.title)
        slug = self.find_available_slug(parent_path, slug)

        self.slug = slug
        self.path = paths.join(parent_path, slug)
        self.path_depth = paths.depth(self.path)

        return self.path

    def find_available_slug(self, parent_path, slug):
        """Append -2, -3... until the resulting path is free among siblings."""
        base = paths.suggest_slug(slug)
        taken = set(
            Page.objects.filter(space=self.space)
            .children_of(parent_path)
            .exclude(pk=self.pk)
            .values_list("slug", flat=True)
        )

        candidate = base
        suffix = 2
        while candidate in taken:
            candidate = f"{base}-{suffix}"
            suffix += 1

        return candidate

    def move_to(self, parent_path, slug=None):
        """
        Move this page (and its whole subtree) under ``parent_path``.

        The subtree is rewritten in a single UPDATE: every descendant's path
        has the old prefix swapped for the new one, and its depth shifted by
        the same delta.
        """
        parent_path = paths.normalise(parent_path)

        if parent_path != paths.ROOT_PATH and not Page.objects.filter(
            space=self.space, path=parent_path
        ).exists():
            raise ValidationError(f"There is no page at '{parent_path}'.")

        if parent_path == self.path or paths.is_descendant_of(parent_path, self.path):
            raise ValidationError("A page can't be moved inside itself.")

        old_path = self.path
        new_path = self.place_under(parent_path, slug)

        if new_path == old_path:
            return self.path

        self.save(update_fields=["slug", "path", "path_depth", "updated_at"])
        self._rewrite_subtree(old_path, new_path)

        return self.path

    def change_slug(self, slug):
        """Rename in place, taking the subtree with it."""
        return self.move_to(paths.parent_of(self.path) or paths.ROOT_PATH, slug=slug)

    def _rewrite_subtree(self, old_path, new_path):
        depth_delta = paths.depth(new_path) - paths.depth(old_path)

        # One UPDATE for the whole subtree. Substr is 1-indexed, so
        # len(old_path) + 1 is the first character after the old prefix.
        return (
            Page.objects.filter(space=self.space, path__startswith=old_path)
            .exclude(pk=self.pk)
            .update(
                path=Concat(
                    models.Value(new_path), Substr("path", len(old_path) + 1)
                ),
                path_depth=models.F("path_depth") + depth_delta,
                # auto_now doesn't fire on a queryset update
                updated_at=timezone.now(),
            )
        )

    # -- Content -----------------------------------------------------------

    def update_content(self, content):
        """Set the draft content and keep the derived title in sync."""
        from .schema import content_to_title

        self.content = content
        self.title = content_to_title(self.content_type, content)

    # -- Publishing --------------------------------------------------------

    @property
    def status(self):
        if self.live:
            return (
                PageStatus.LIVE_PLUS_DRAFT
                if self.has_unpublished_changes
                else PageStatus.LIVE
            )
        return PageStatus.UNPUBLISHED if self.first_published_at else PageStatus.DRAFT

    @property
    def status_label(self):
        return PageStatus(self.status).label

    def save_revision(self, user=None):
        """Snapshot the current draft content as a new revision."""
        revision = PageRevision.objects.create(
            page=self,
            content=self.content,
            title=self.title,
            created_by=user if user is not None and user.is_authenticated else None,
        )

        self.latest_revision = revision
        self.has_unpublished_changes = self.live and revision != self.live_revision
        self.save(
            update_fields=["latest_revision", "has_unpublished_changes", "updated_at"]
        )

        return revision

    def publish(self, revision=None):
        """Make a revision (by default the latest draft) the live version."""
        revision = revision or self.latest_revision
        if revision is None:
            revision = self.save_revision()

        now = timezone.now()

        self.live_revision = revision
        self.live = True
        self.has_unpublished_changes = revision != self.latest_revision
        self.last_published_at = now
        if self.first_published_at is None:
            self.first_published_at = now

        self.save(
            update_fields=[
                "live_revision",
                "live",
                "has_unpublished_changes",
                "first_published_at",
                "last_published_at",
                "updated_at",
            ]
        )

        return revision

    def unpublish(self):
        self.live = False
        self.has_unpublished_changes = self.latest_revision != self.live_revision
        self.save(update_fields=["live", "has_unpublished_changes", "updated_at"])

    def revert_to_revision(self, revision, user=None):
        """Copy an old revision's content back into the draft."""
        self.content = revision.content
        self.title = revision.title
        self.save(update_fields=["content", "title", "updated_at"])
        return self.save_revision(user=user)

    @property
    def live_content(self):
        """What the public site would serve, or ``None`` if not published."""
        if not self.live or self.live_revision is None:
            return None
        return self.live_revision.content


class PageRevision(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid7)
    page = models.ForeignKey(Page, on_delete=models.CASCADE, related_name="revisions")
    content = models.JSONField()
    title = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="page_revisions",
    )

    class Meta:
        db_table = "djangopress_pagerevision"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.title} @ {self.created_at:%Y-%m-%d %H:%M}"

    @property
    def is_live(self):
        return self.page.live_revision_id == self.id

    @property
    def is_latest(self):
        return self.page.latest_revision_id == self.id
