from django.http import Http404
from django.shortcuts import redirect
from django.utils.text import slugify

from .models import Space, SpaceUser


def default_space_redirect(request):
    space = Space.objects.filter(users=request.user).first()

    if space is None:
        # A freshly created superuser has no space. Rather than blowing up with
        # an AttributeError, give them one.
        space = Space.objects.create(
            name=f"{request.user.get_username()}'s space",
            slug=slugify(request.user.get_username()) or "default",
        )
        SpaceUser.objects.create(space=space, user=request.user)

    return redirect("home", space.slug)
