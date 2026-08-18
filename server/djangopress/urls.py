from django.contrib import admin
from django.contrib.auth.decorators import login_required
from django.urls import include, path
from django.conf.urls.static import static
from django.conf import settings

from . import views
from .auth import views as auth_views
from .files import views as files_views
from .pages import content_type_views, views as pages_views
from .utils import decorate_urlpatterns
from .spaces.decorators import space_from_url
from .spaces import views as spaces_views

# Put any space-specific URLs here
urlpatterns_space = [
    path("", views.home, name="home"),
    # Pages
    path("pages/", pages_views.index, name="pages_index"),
    path(
        "pages/choose-type/",
        pages_views.choose_content_type,
        name="pages_choose_content_type",
    ),
    path("pages/add/<int:content_type_id>/", pages_views.add, name="pages_add"),
    path("pages/<uuid:page_id>/edit/", pages_views.edit, name="pages_edit"),
    path("pages/<uuid:page_id>/delete/", pages_views.delete, name="pages_delete"),
    path("pages/<uuid:page_id>/move/", pages_views.move, name="pages_move"),
    path(
        "pages/<uuid:page_id>/unpublish/",
        pages_views.unpublish,
        name="pages_unpublish",
    ),
    path(
        "pages/<uuid:page_id>/revisions/",
        pages_views.revisions,
        name="pages_revisions",
    ),
    path(
        "pages/<uuid:page_id>/revisions/<uuid:revision_id>/revert/",
        pages_views.revert,
        name="pages_revert",
    ),
    # Content types
    path("content-types/", content_type_views.index, name="content_types_index"),
    path("content-types/add/", content_type_views.add, name="content_types_add"),
    path(
        "content-types/<int:content_type_id>/edit/",
        content_type_views.edit,
        name="content_types_edit",
    ),
    path(
        "content-types/<int:content_type_id>/delete/",
        content_type_views.delete,
        name="content_types_delete",
    ),
    # Files
    path("files/", files_views.index, name="files_index"),
    path("files/upload/", files_views.upload, name="files_upload"),
    path("files/<uuid:file_id>/edit/", files_views.edit, name="files_edit"),
    path("files/<uuid:file_id>/delete/", files_views.delete, name="files_delete"),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


# Put any URLs that require authentication in this list.
urlpatterns_auth = [
    path("admin/", admin.site.urls),
    path("", spaces_views.default_space_redirect),
    # Spaces
    path(
        "<str:space_slug>/",
        include(decorate_urlpatterns(urlpatterns_space, space_from_url)),
    ),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Put any URLs that do not require authentication in this list.
urlpatterns_noauth = [
    path("login/", auth_views.LoginView.as_view(), name="login"),
]

if settings.DEMO_MODE:
    urlpatterns_noauth += [
        path("login-temporary/", auth_views.login_temporary, name="login_temporary"),
    ]

urlpatterns = urlpatterns_noauth + decorate_urlpatterns(
    urlpatterns_auth, login_required
)
