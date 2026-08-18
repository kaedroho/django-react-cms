from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.text import slugify
from uuid_extensions import uuid7

from djangopress.spaces.models import Space


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

    def get_form_class(self):
        """
        Builds a Django Form class from this content type's schema.

        See ``djangopress.pages.schema`` --- this is the heart of the CMS.
        """
        from .schema import build_form_class

        return build_form_class(self)

    @property
    def field_count(self):
        return len(self.schema.get("fields", []))


class PageStatus(models.TextChoices):
    DRAFT = "draft", "Draft"
    LIVE = "live", "Live"
    LIVE_PLUS_DRAFT = "live+draft", "Live + draft"
    UNPUBLISHED = "unpublished", "Unpublished"


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
    path = models.TextField()
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

    class Meta:
        db_table = "djangopress_page"
        unique_together = [("space", "path")]
        ordering = ["-updated_at"]

    def __str__(self):
        return self.title

    # -- Content -----------------------------------------------------------

    def update_content(self, content):
        """Set the draft content, and keep the derived title and path in sync."""
        from .schema import content_to_title

        self.content = content
        self.title = content_to_title(self.content_type, content)

        if not self.slug:
            self.set_slug_from_title()

        self.path = self.slug

    def set_slug_from_title(self):
        base = slugify(self.title) or "page"
        slug = base

        existing = set(
            Page.objects.filter(space=self.space)
            .exclude(pk=self.pk)
            .values_list("slug", flat=True)
        )

        suffix = 2
        while slug in existing:
            slug = f"{base}-{suffix}"
            suffix += 1

        self.slug = slug
        self.path = slug

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
