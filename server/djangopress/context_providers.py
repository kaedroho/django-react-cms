from django.urls import reverse


def urls(request):
    space = getattr(request, "space", None)

    if space:
        return {
            "pages_index": reverse("pages_index", args=[space.slug]),
            "files_index": reverse("files_index", args=[space.slug]),
            "content_types_index": reverse("content_types_index", args=[space.slug]),
        }

    else:
        return {}
