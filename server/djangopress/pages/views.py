from django.contrib import messages
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils.timesince import timesince
from django_bridge.metadata import Metadata
from django_bridge.response import CloseOverlayResponse, RedirectResponse, Response

from .models import Page, PageContentType, PageRevision
from .schema import cleaned_data_to_content, content_to_form_initial


def _page_props(page):
    return {
        "id": str(page.id),
        "title": page.title,
        "path": page.path,
        "content_type": page.content_type.name,
        "status": page.status,
        "status_label": page.status_label,
        "live": page.live,
        "has_unpublished_changes": page.has_unpublished_changes,
        "updated_at": timesince(page.updated_at) + " ago",
        "edit_url": reverse("pages_edit", args=[page.space.slug, str(page.id)]),
        "delete_url": reverse("pages_delete", args=[page.space.slug, str(page.id)]),
        "revisions_url": reverse(
            "pages_revisions", args=[page.space.slug, str(page.id)]
        ),
        "unpublish_url": reverse(
            "pages_unpublish", args=[page.space.slug, str(page.id)]
        ),
    }


def index(request):
    pages = Page.objects.filter(space=request.space).select_related(
        "content_type", "space"
    )

    return Response(
        request,
        "PagesIndex",
        {
            "pages": [_page_props(page) for page in pages],
            "choose_content_type_url": reverse(
                "pages_choose_content_type", args=[request.space.slug]
            ),
            "content_types_index_url": reverse(
                "content_types_index", args=[request.space.slug]
            ),
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
    content_types = PageContentType.objects.filter(space=request.space)

    return Response(
        request,
        "ChooseContentType",
        {
            "content_types": [
                {
                    "id": content_type.id,
                    "name": content_type.name,
                    "field_count": content_type.field_count,
                    "add_url": reverse(
                        "pages_add", args=[request.space.slug, content_type.id]
                    ),
                }
                for content_type in content_types
            ],
            "content_types_add_url": reverse(
                "content_types_add", args=[request.space.slug]
            ),
        },
        overlay=True,
        metadata=Metadata(title="Choose a page type | Djangopress"),
    )


def add(request, content_type_id):
    content_type = get_object_or_404(
        PageContentType, space=request.space, id=content_type_id
    )

    # The form class is built from the content type's schema at request time.
    form_class = content_type.get_form_class()
    form = form_class(request.POST or None)

    if form.is_valid():
        publish = "publish" in request.POST

        page = Page(space=request.space, content_type=content_type, content={})
        page.update_content(cleaned_data_to_content(content_type, form.cleaned_data))
        page.set_slug_from_title()
        page.save()
        page.save_revision(user=request.user)

        if publish:
            page.publish()

        messages.success(
            request,
            f"{'Published' if publish else 'Created'} page '{page.title}'.",
        )

        return CloseOverlayResponse(request)

    return Response(
        request,
        "PageForm",
        {
            "page": None,
            "content_type": content_type.name,
            "action_url": reverse(
                "pages_add", args=[request.space.slug, content_type.id]
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

    form_class = content_type.get_form_class()
    form = form_class(
        request.POST or None,
        initial=content_to_form_initial(content_type, page.content),
    )

    if form.is_valid():
        publish = "publish" in request.POST

        page.update_content(cleaned_data_to_content(content_type, form.cleaned_data))
        page.save()
        page.save_revision(user=request.user)

        if publish:
            page.publish()
            messages.success(request, f"Published page '{page.title}'.")
        else:
            messages.success(request, f"Saved draft of page '{page.title}'.")

        # Re-bind to the saved content so the form doesn't show stale values
        form = form_class(initial=content_to_form_initial(content_type, page.content))

    return Response(
        request,
        "PageForm",
        {
            "page": _page_props(page),
            "content_type": content_type.name,
            "action_url": reverse(
                "pages_edit", args=[request.space.slug, str(page.id)]
            ),
            "form": form,
        },
        metadata=Metadata(title=f"Editing {page.title} | Djangopress"),
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
            "actionUrl": reverse(
                "pages_unpublish", args=[request.space.slug, str(page.id)]
            ),
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
                    "revert_url": reverse(
                        "pages_revert",
                        args=[request.space.slug, str(page.id), str(revision.id)],
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

    return RedirectResponse(
        reverse("pages_revisions", args=[request.space.slug, str(page.id)])
    )


def delete(request, page_id):
    page = get_object_or_404(Page, space=request.space, id=page_id)

    if request.method == "POST":
        title = page.title
        page.delete()

        messages.success(request, f"Successfully deleted page '{title}'.")

        return CloseOverlayResponse(request)

    return Response(
        request,
        "ConfirmDelete",
        {
            "objectName": page.title,
            "messageHtml": (
                "Are you sure that you want to delete this page? "
                "Its revision history will be deleted too."
            ),
            "actionUrl": reverse(
                "pages_delete", args=[request.space.slug, str(page.id)]
            ),
        },
        overlay=True,
        metadata=Metadata(title=f"Delete {page.title} | Djangopress"),
    )
