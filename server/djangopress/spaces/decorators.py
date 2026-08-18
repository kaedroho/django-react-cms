from functools import wraps

from django.http import Http404

from .models import Space


def space_from_url(fn):
    """
    Adds the Space to the request object by taking the space slug from
    the first URL argument.
    """

    @wraps(fn)
    def wrapper(request, space_slug, *args, **kwargs):
        try:
            space = Space.objects.get(users=request.user, slug=space_slug)
        except Space.DoesNotExist:
            raise Http404(f"No space '{space_slug}' available to this user")
        else:
            request.space = space
            return fn(request, *args, **kwargs)

    return wrapper
