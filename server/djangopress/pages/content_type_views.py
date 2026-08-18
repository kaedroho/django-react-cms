"""
CRUD for content types themselves.

Editing a content type changes the shape of the page editor for every page of
that type --- without a migration, a deploy, or a single line of React.
"""

from django.contrib import messages
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django_bridge.metadata import Metadata
from django_bridge.response import CloseOverlayResponse, Response

from .forms import ContentTypeForm
from .models import PageContentType


def _content_type_props(content_type, space):
    return {
        "id": content_type.id,
        "name": content_type.name,
        "field_count": content_type.field_count,
        "page_count": content_type.pages.count(),
        "fields": [
            {
                "name": field.get("name"),
                "label": field.get("label") or field.get("name"),
                "type": field.get("type"),
                "required": bool(field.get("required")),
            }
            for field in content_type.schema.get("fields", [])
        ],
        "edit_url": reverse("content_types_edit", args=[space.slug, content_type.id]),
        "delete_url": reverse(
            "content_types_delete", args=[space.slug, content_type.id]
        ),
    }


def index(request):
    content_types = PageContentType.objects.filter(space=request.space)

    return Response(
        request,
        "ContentTypesIndex",
        {
            "content_types": [
                _content_type_props(content_type, request.space)
                for content_type in content_types
            ],
            "add_url": reverse("content_types_add", args=[request.space.slug]),
        },
        metadata=Metadata(title="Content types | Djangopress"),
    )


def add(request):
    form = ContentTypeForm(request.POST or None, space=request.space)

    if form.is_valid():
        content_type = form.save(commit=False)
        content_type.space = request.space
        content_type.save()

        messages.success(request, f"Created content type '{content_type.name}'.")

        return CloseOverlayResponse(request)

    return Response(
        request,
        "ContentTypeForm",
        {
            "content_type": None,
            "action_url": reverse("content_types_add", args=[request.space.slug]),
            "form": form,
        },
        overlay=True,
        metadata=Metadata(title="New content type | Djangopress"),
    )


def edit(request, content_type_id):
    content_type = get_object_or_404(
        PageContentType, space=request.space, id=content_type_id
    )
    form = ContentTypeForm(
        request.POST or None, instance=content_type, space=request.space
    )

    if form.is_valid():
        form.save()

        messages.success(request, f"Updated content type '{content_type.name}'.")

        return CloseOverlayResponse(request)

    return Response(
        request,
        "ContentTypeForm",
        {
            "content_type": _content_type_props(content_type, request.space),
            "action_url": reverse(
                "content_types_edit", args=[request.space.slug, content_type.id]
            ),
            "form": form,
        },
        overlay=True,
        metadata=Metadata(title=f"Editing {content_type.name} | Djangopress"),
    )


def delete(request, content_type_id):
    content_type = get_object_or_404(
        PageContentType, space=request.space, id=content_type_id
    )
    page_count = content_type.pages.count()

    if request.method == "POST":
        name = content_type.name
        content_type.delete()

        messages.success(request, f"Deleted content type '{name}'.")

        return CloseOverlayResponse(request)

    if page_count:
        message = (
            f"<strong>{page_count} page(s)</strong> use this content type and will "
            "be deleted along with it."
        )
    else:
        message = "No pages use this content type."

    return Response(
        request,
        "ConfirmDelete",
        {
            "objectName": content_type.name,
            "messageHtml": message,
            "actionUrl": reverse(
                "content_types_delete", args=[request.space.slug, content_type.id]
            ),
        },
        overlay=True,
        metadata=Metadata(title=f"Delete {content_type.name} | Djangopress"),
    )
