from collections import Counter

from django.contrib import messages
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils.http import urlencode
from django.utils.timesince import timesince
from django_bridge.metadata import Metadata
from django_bridge.response import CloseOverlayResponse, RedirectResponse, Response

from . import paths
from .models import Page, PageContentType, PageRevision
from .schema import cleaned_data_to_content, content_to_form_initial


def _url(name, space, *args, **params):
    url = reverse(name, args=[space.slug, *args])
    return f"{url}?{urlencode(params)}" if params else url


def _page_props(page, child_count=None):
    space = page.space

    return {
        "id": str(page.id),
        "title": page.title,
        "path": page.path,
        "slug": page.slug,
        "depth": page.path_depth,
        "content_type": page.content_type.name,
        "status": page.status,
        "status_label": page.status_label,
        "live": page.live,
        "has_unpublished_changes": page.has_unpublished_changes,
        "updated_at": timesince(page.updated_at) + " ago",
        "child_count": child_count,
        "children_url": _url("pages_index", space, parent=page.path),
        "edit_url": _url("pages_edit", space, str(page.id)),
        "delete_url": _url("pages_delete", space, str(page.id)),
        "move_url": _url("pages_move", space, str(page.id)),
        "revisions_url": _url("pages_revisions", space, str(page.id)),
        "unpublish_url": _url("pages_unpublish", space, str(page.id)),
    }


def _breadcrumb(space, parent_path):
    """Ancestor pages of the location being browsed, root first."""
    ancestors = {
        page.path: page
        for page in Page.objects.filter(space=space).ancestors_of(
            parent_path, inclusive=True
        )
    }

    crumbs = [{"label": "Root", "path": paths.ROOT_PATH, "url": _url("pages_index", space)}]

    for path in paths.ancestors_of(parent_path, inclusive=True)[1:]:
        page = ancestors.get(path)
        crumbs.append(
            {
                "label": page.title if page else paths.slug_of(path),
                "path": path,
                "url": _url("pages_index", space, parent=path),
            }
        )

    return crumbs


def _child_counts(space, parent_path):
    """
    How many children each child has, in one extra query.

    Fetches the grandchildren's paths and tallies them by parent in Python.
    A denormalised ``numchild`` column is the answer if this ever gets hot;
    at one level of a drill-down explorer it isn't worth the write cost.
    """
    grandchild_paths = (
        Page.objects.filter(space=space)
        .filter(
            path__startswith=paths.normalise(parent_path),
            path_depth=paths.depth(parent_path) + 2,
        )
        .values_list("path", flat=True)
    )

    return Counter(paths.parent_of(path) for path in grandchild_paths)


def index(request):
    parent_path = paths.normalise(request.GET.get("parent"))
    parent = Page.objects.filter(space=request.space, path=parent_path).first()

    if parent is None and parent_path != paths.ROOT_PATH:
        # Browsing somewhere that no longer exists (a page was moved or
        # deleted) --- fall back to the root rather than 404ing the listing.
        return RedirectResponse(_url("pages_index", request.space))

    children = (
        Page.objects.filter(space=request.space)
        .children_of(parent_path)
        .select_related("content_type", "space")
    )
    child_counts = _child_counts(request.space, parent_path)

    return Response(
        request,
        "PagesIndex",
        {
            "parent": _page_props(parent) if parent else None,
            "parent_path": parent_path,
            "breadcrumb": _breadcrumb(request.space, parent_path),
            "pages": [
                _page_props(page, child_count=child_counts.get(page.path, 0))
                for page in children
            ],
            "choose_content_type_url": _url(
                "pages_choose_content_type", request.space, parent=parent_path
            ),
            "content_types_index_url": _url("content_types_index", request.space),
            "has_content_types": PageContentType.objects.filter(
                space=request.space
            ).exists(),
        },
        metadata=Metadata(title="Pages | Djangopress"),
    )


def choose_content_type(request):
    """
    Step one of adding a page: pick what kind of page it is.

    This renders inside the same overlay the "Add page" button opens, and
    picking a type navigates the overlay on to the add form.
    """
    parent_path = paths.normalise(request.GET.get("parent"))
    content_types = PageContentType.objects.filter(space=request.space)

    return Response(
        request,
        "ChooseContentType",
        {
            "parent_path": parent_path,
            "content_types": [
                {
                    "id": content_type.id,
                    "name": content_type.name,
                    "field_count": content_type.field_count,
                    "add_url": _url(
                        "pages_add",
                        request.space,
                        content_type.id,
                        parent=parent_path,
                    ),
                }
                for content_type in content_types
            ],
            "content_types_add_url": _url("content_types_add", request.space),
        },
        overlay=True,
        metadata=Metadata(title="Choose a page type | Djangopress"),
    )


def add(request, content_type_id):
    content_type = get_object_or_404(
        PageContentType, space=request.space, id=content_type_id
    )
    parent_path = paths.normalise(request.GET.get("parent"))

    # The form class is built from the content type's schema at request time.
    form_class = content_type.get_form_class(include_slug=True)
    form = form_class(request.POST or None)

    if form.is_valid():
        publish = "publish" in request.POST

        page = Page(space=request.space, content_type=content_type, content={})
        page.update_content(cleaned_data_to_content(content_type, form.cleaned_data))
        page.place_under(parent_path, slug=form.cleaned_data.get("slug") or None)
        page.save()
        page.save_revision(user=request.user)

        if publish:
            page.publish()

        messages.success(
            request,
            f"{'Published' if publish else 'Created'} page '{page.title}' at {page.path}",
        )

        return CloseOverlayResponse(request)

    return Response(
        request,
        "PageForm",
        {
            "page": None,
            "parent_path": parent_path,
            "content_type": content_type.name,
            "action_url": _url(
                "pages_add", request.space, content_type.id, parent=parent_path
            ),
            "form": form,
        },
        overlay=True,
        metadata=Metadata(title=f"New {content_type.name} | Djangopress"),
    )


def edit(request, page_id):
    page = get_object_or_404(
        Page.objects.select_related("content_type", "space"),
        space=request.space,
        id=page_id,
    )
    content_type = page.content_type

    form_class = content_type.get_form_class(include_slug=True)
    initial = content_to_form_initial(content_type, page.content)
    initial["slug"] = page.slug
    form = form_class(request.POST or None, initial=initial)

    if form.is_valid():
        publish = "publish" in request.POST

        page.update_content(cleaned_data_to_content(content_type, form.cleaned_data))
        page.save()

        new_slug = form.cleaned_data.get("slug")
        moved = 0
        if new_slug and new_slug != page.slug:
            # Renaming takes the whole subtree with it
            moved = page.get_descendants().count()
            page.change_slug(new_slug)

        page.save_revision(user=request.user)

        if publish:
            page.publish()
            messages.success(request, f"Published page '{page.title}'.")
        else:
            messages.success(request, f"Saved draft of page '{page.title}'.")

        if moved:
            messages.success(
                request,
                f"Moved {moved} page(s) underneath it to match the new URL.",
            )

        # Re-bind to the saved content so the form doesn't show stale values
        initial = content_to_form_initial(content_type, page.content)
        initial["slug"] = page.slug
        form = form_class(initial=initial)

    return Response(
        request,
        "PageForm",
        {
            "page": _page_props(page, child_count=page.get_children().count()),
            "parent_path": paths.parent_of(page.path),
            "breadcrumb": _breadcrumb(request.space, paths.parent_of(page.path)),
            "content_type": content_type.name,
            "action_url": _url("pages_edit", request.space, str(page.id)),
            "form": form,
        },
        metadata=Metadata(title=f"Editing {page.title} | Djangopress"),
    )


def move(request, page_id):
    """
    Re-parent a page. The whole subtree comes along, rewritten in one UPDATE.

    Candidate destinations are every page that isn't the page itself or one of
    its descendants --- moving a page inside its own subtree is the one thing
    the path scheme can't represent.
    """
    page = get_object_or_404(
        Page.objects.select_related("space"), space=request.space, id=page_id
    )
    error = None

    if request.method == "POST":
        destination = paths.normalise(request.POST.get("destination"))
        try:
            page.move_to(destination)
        except ValidationError as e:
            error = e.messages[0]
        else:
            messages.success(request, f"Moved '{page.title}' to {page.path}")
            return CloseOverlayResponse(request)

    candidates = [
        {
            "path": paths.ROOT_PATH,
            "label": "Root",
            "depth": 0,
            "current": paths.parent_of(page.path) == paths.ROOT_PATH,
        }
    ]
    for candidate in Page.objects.filter(space=request.space).exclude(
        path__startswith=page.path
    ):
        candidates.append(
            {
                "path": candidate.path,
                "label": candidate.title,
                "depth": candidate.path_depth,
                "current": paths.parent_of(page.path) == candidate.path,
            }
        )

    return Response(
        request,
        "MovePage",
        {
            "page": _page_props(page, child_count=page.get_children().count()),
            "descendant_count": page.get_descendants().count(),
            "candidates": candidates,
            "action_url": _url("pages_move", request.space, str(page.id)),
            "error": error,
        },
        overlay=True,
        metadata=Metadata(title=f"Move {page.title} | Djangopress"),
    )


def unpublish(request, page_id):
    page = get_object_or_404(Page, space=request.space, id=page_id)

    if request.method == "POST":
        page.unpublish()
        messages.success(request, f"Unpublished page '{page.title}'.")
        return CloseOverlayResponse(request)

    return Response(
        request,
        "ConfirmDelete",
        {
            "objectName": page.title,
            "messageHtml": (
                "This page will no longer be visible on the site. "
                "The draft will be kept."
            ),
            "actionUrl": _url("pages_unpublish", request.space, str(page.id)),
            "confirmLabel": "Unpublish",
        },
        overlay=True,
        metadata=Metadata(title=f"Unpublish {page.title} | Djangopress"),
    )


def revisions(request, page_id):
    page = get_object_or_404(
        Page.objects.select_related("space"), space=request.space, id=page_id
    )

    return Response(
        request,
        "PageRevisions",
        {
            "page": _page_props(page),
            "revisions": [
                {
                    "id": str(revision.id),
                    "title": revision.title,
                    "created_at": timesince(revision.created_at) + " ago",
                    "created_by": (
                        revision.created_by.get_username()
                        if revision.created_by
                        else "Unknown"
                    ),
                    "is_live": revision.id == page.live_revision_id,
                    "is_latest": revision.id == page.latest_revision_id,
                    "revert_url": _url(
                        "pages_revert", request.space, str(page.id), str(revision.id)
                    ),
                }
                for revision in page.revisions.select_related("created_by")[:50]
            ],
        },
        overlay=True,
        metadata=Metadata(title=f"History of {page.title} | Djangopress"),
    )


def revert(request, page_id, revision_id):
    page = get_object_or_404(Page, space=request.space, id=page_id)
    revision = get_object_or_404(PageRevision, page=page, id=revision_id)

    if request.method == "POST":
        page.revert_to_revision(revision, user=request.user)
        messages.success(
            request,
            f"Restored '{page.title}' to the version from {revision.created_at:%d %b %Y, %H:%M}. "
            "This is now the draft --- publish it to make it live.",
        )
        return CloseOverlayResponse(request)

    return RedirectResponse(_url("pages_revisions", request.space, str(page.id)))


def delete(request, page_id):
    page = get_object_or_404(
        Page.objects.select_related("space"), space=request.space, id=page_id
    )
    descendant_count = page.get_descendants().count()

    if request.method == "POST":
        title = page.title
        # Descendants would be orphaned by a path scheme that has no parent
        # FK to cascade through, so remove the subtree explicitly.
        page.get_descendants(inclusive=True).delete()

        messages.success(request, f"Successfully deleted page '{title}'.")

        return CloseOverlayResponse(request)

    if descendant_count:
        message = (
            f"<strong>{descendant_count} page(s) underneath it</strong> will be "
            "deleted too, along with all revision history."
        )
    else:
        message = (
            "Are you sure that you want to delete this page? "
            "Its revision history will be deleted too."
        )

    return Response(
        request,
        "ConfirmDelete",
        {
            "objectName": page.title,
            "messageHtml": message,
            "actionUrl": _url("pages_delete", request.space, str(page.id)),
        },
        overlay=True,
        metadata=Metadata(title=f"Delete {page.title} | Djangopress"),
    )
