"""
Tests for schema-driven content types and the publishing workflow.

Worth reading as a demo in its own right: because Django Bridge views are
ordinary Django views, testing a CMS publish flow end-to-end is a normal
Django ``TestCase``. ``response.props`` gives back the *Python* objects the
view passed to React, before serialisation --- so there's no JSON parsing, no
mock service worker, and no React test renderer anywhere in this file.
"""

import copy
import json

from django.core.exceptions import ValidationError
from django.urls import reverse
from django_bridge.test import TestCase

from djangopress.auth.models import User
from djangopress.pages.models import Page, PageContentType, PageStatus
from djangopress.pages.schema import (
    build_form_class,
    cleaned_data_to_content,
    content_to_title,
    validate_schema,
)
from djangopress.spaces.models import Space, SpaceUser


BLOG_POST_SCHEMA = {
    "title_field": "title",
    "fields": [
        {"name": "title", "type": "text", "required": True},
        {"name": "summary", "type": "long_text"},
        {"name": "body", "type": "rich_text"},
        {"name": "published_on", "type": "date"},
        {"name": "featured", "type": "boolean"},
    ],
}


class SchemaTestCase(TestCase):
    def setUp(self):
        self.space = Space.objects.create(name="Test", slug="test")
        self.content_type = PageContentType.objects.create(
            space=self.space,
            name="Blog post",
            schema=copy.deepcopy(BLOG_POST_SCHEMA),
        )

    def test_form_is_built_from_schema(self):
        form_class = build_form_class(self.content_type)
        form = form_class()

        self.assertEqual(
            list(form.fields), ["title", "summary", "body", "published_on", "featured"]
        )
        self.assertTrue(form.fields["title"].required)
        # A checkbox that must be ticked is never what anyone means
        self.assertFalse(form.fields["featured"].required)

    def test_adding_a_field_to_the_schema_adds_it_to_the_form(self):
        """The whole point: no code change, no migration, no deploy."""
        self.content_type.schema["fields"].append({"name": "author", "type": "text"})
        self.content_type.save()

        form = self.content_type.get_form_class()()

        self.assertIn("author", form.fields)

    def test_rich_text_is_stored_as_json_not_a_string(self):
        form_class = build_form_class(self.content_type)
        form = form_class(
            {
                "title": "Hello",
                "body": json.dumps(
                    [{"type": "paragraph", "content": [{"type": "text", "text": "Hi"}]}]
                ),
            }
        )

        self.assertTrue(form.is_valid(), form.errors)
        content = cleaned_data_to_content(self.content_type, form.cleaned_data)

        self.assertIsInstance(content["fields"]["body"], list)

    def test_title_is_derived_from_the_schemas_title_field(self):
        title = content_to_title(self.content_type, {"fields": {"title": "My post"}})

        self.assertEqual(title, "My post")

    def test_title_falls_back_when_the_title_field_is_empty(self):
        title = content_to_title(self.content_type, {"fields": {"title": ""}})

        self.assertEqual(title, "Untitled")

    def test_validate_schema_rejects_unknown_field_types(self):
        with self.assertRaises(ValidationError):
            validate_schema({"fields": [{"name": "x", "type": "wormhole"}]})

    def test_validate_schema_rejects_duplicate_names(self):
        with self.assertRaises(ValidationError):
            validate_schema(
                {
                    "fields": [
                        {"name": "title", "type": "text"},
                        {"name": "title", "type": "text"},
                    ]
                }
            )

    def test_validate_schema_rejects_a_title_field_that_doesnt_exist(self):
        with self.assertRaises(ValidationError):
            validate_schema(
                {
                    "title_field": "nope",
                    "fields": [{"name": "title", "type": "text"}],
                }
            )


class PublishingTestCase(TestCase):
    def setUp(self):
        self.space = Space.objects.create(name="Test", slug="test")
        self.content_type = PageContentType.objects.create(
            space=self.space,
            name="Blog post",
            schema=copy.deepcopy(BLOG_POST_SCHEMA),
        )
        self.page = Page(
            space=self.space, content_type=self.content_type, content={}
        )
        self.page.update_content({"fields": {"title": "First post"}})
        self.page.set_slug_from_title()
        self.page.save()

    def test_a_new_page_is_a_draft(self):
        self.assertEqual(self.page.status, PageStatus.DRAFT)
        self.assertIsNone(self.page.live_content)

    def test_publishing_makes_content_live(self):
        self.page.save_revision()
        self.page.publish()

        self.assertEqual(self.page.status, PageStatus.LIVE)
        self.assertEqual(self.page.live_content["fields"]["title"], "First post")

    def test_editing_a_live_page_leaves_the_live_version_alone(self):
        self.page.save_revision()
        self.page.publish()

        self.page.update_content({"fields": {"title": "Second draft"}})
        self.page.save()
        self.page.save_revision()

        self.assertEqual(self.page.status, PageStatus.LIVE_PLUS_DRAFT)
        self.assertEqual(self.page.content["fields"]["title"], "Second draft")
        self.assertEqual(self.page.live_content["fields"]["title"], "First post")

    def test_publishing_again_promotes_the_draft(self):
        self.page.save_revision()
        self.page.publish()
        self.page.update_content({"fields": {"title": "Second draft"}})
        self.page.save()
        self.page.save_revision()
        self.page.publish()

        self.assertEqual(self.page.status, PageStatus.LIVE)
        self.assertEqual(self.page.live_content["fields"]["title"], "Second draft")

    def test_unpublishing_keeps_the_draft(self):
        self.page.save_revision()
        self.page.publish()
        self.page.unpublish()

        self.assertEqual(self.page.status, PageStatus.UNPUBLISHED)
        self.assertIsNone(self.page.live_content)
        self.assertEqual(self.page.content["fields"]["title"], "First post")

    def test_reverting_restores_old_content_as_a_draft(self):
        first = self.page.save_revision()
        self.page.publish()
        self.page.update_content({"fields": {"title": "Regrettable edit"}})
        self.page.save()
        self.page.save_revision()

        self.page.revert_to_revision(first)

        self.assertEqual(self.page.content["fields"]["title"], "First post")
        self.assertEqual(self.page.live_content["fields"]["title"], "First post")
        # Reverting is a draft operation: it creates a new revision rather than
        # republishing, so the page still reports outstanding draft changes
        self.assertEqual(self.page.status, PageStatus.LIVE_PLUS_DRAFT)

    def test_slugs_do_not_collide(self):
        other = Page(space=self.space, content_type=self.content_type, content={})
        other.update_content({"fields": {"title": "First post"}})
        other.set_slug_from_title()
        other.save()

        self.assertEqual(other.slug, "first-post-2")


class PageViewsTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("editor", password="hunter2")
        self.space = Space.objects.create(name="Test", slug="test")
        SpaceUser.objects.create(space=self.space, user=self.user)
        self.content_type = PageContentType.objects.create(
            space=self.space,
            name="Blog post",
            schema=copy.deepcopy(BLOG_POST_SCHEMA),
        )
        self.client.force_login(self.user)

    def add_url(self):
        return reverse("pages_add", args=[self.space.slug, self.content_type.id])

    def test_the_add_form_has_the_schemas_fields(self):
        response = self.client.get(self.add_url())

        # response.props holds the Python objects the view passed to React
        form = response.props["form"]
        self.assertEqual(
            list(form.fields), ["title", "summary", "body", "published_on", "featured"]
        )

    def test_save_draft_creates_an_unpublished_page(self):
        self.client.post(self.add_url(), {"title": "Draft post"})

        page = Page.objects.get(space=self.space)
        self.assertEqual(page.title, "Draft post")
        self.assertEqual(page.status, PageStatus.DRAFT)
        self.assertEqual(page.revisions.count(), 1)

    def test_publish_button_publishes(self):
        self.client.post(self.add_url(), {"title": "Live post", "publish": "1"})

        page = Page.objects.get(space=self.space)
        self.assertEqual(page.status, PageStatus.LIVE)
        self.assertIsNotNone(page.first_published_at)

    def test_editing_a_live_page_creates_a_draft(self):
        self.client.post(self.add_url(), {"title": "Live post", "publish": "1"})
        page = Page.objects.get(space=self.space)

        self.client.post(
            reverse("pages_edit", args=[self.space.slug, str(page.id)]),
            {"title": "Edited"},
        )

        page.refresh_from_db()
        self.assertEqual(page.status, PageStatus.LIVE_PLUS_DRAFT)
        self.assertEqual(page.live_content["fields"]["title"], "Live post")

    def test_invalid_submissions_are_redisplayed_with_errors(self):
        response = self.client.post(self.add_url(), {"title": ""})

        self.assertFalse(Page.objects.exists())
        self.assertIn("title", response.props["form"].errors)

    def test_the_pages_index_reports_status(self):
        self.client.post(self.add_url(), {"title": "Live post", "publish": "1"})

        response = self.client.get(reverse("pages_index", args=[self.space.slug]))

        self.assertEqual(len(response.props["pages"]), 1)
        self.assertEqual(response.props["pages"][0]["status_label"], "Live")

    def test_pages_from_another_space_are_not_visible(self):
        other_space = Space.objects.create(name="Other", slug="other")
        other_type = PageContentType.objects.create(
            space=other_space, name="Blog post", schema=BLOG_POST_SCHEMA
        )
        page = Page(space=other_space, content_type=other_type, content={})
        page.update_content({"fields": {"title": "Secret"}})
        page.set_slug_from_title()
        page.save()

        response = self.client.get(reverse("pages_index", args=[self.space.slug]))

        self.assertEqual(response.props["pages"], [])

    def test_revert_from_the_revisions_view(self):
        self.client.post(self.add_url(), {"title": "Version one", "publish": "1"})
        page = Page.objects.get(space=self.space)
        first_revision = page.latest_revision

        self.client.post(
            reverse("pages_edit", args=[self.space.slug, str(page.id)]),
            {"title": "Version two"},
        )
        self.client.post(
            reverse(
                "pages_revert",
                args=[self.space.slug, str(page.id), str(first_revision.id)],
            )
        )

        page.refresh_from_db()
        self.assertEqual(page.title, "Version one")


class ContentTypeViewsTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("editor", password="hunter2")
        self.space = Space.objects.create(name="Test", slug="test")
        SpaceUser.objects.create(space=self.space, user=self.user)
        self.client.force_login(self.user)

    def test_creating_a_content_type(self):
        response = self.client.post(
            reverse("content_types_add", args=[self.space.slug]),
            {
                "name": "Recipe",
                "schema": json.dumps(
                    {
                        "title_field": "name",
                        "fields": [
                            {"name": "name", "type": "text", "required": True},
                            {"name": "method", "type": "rich_text"},
                        ],
                    }
                ),
            },
        )

        self.assertEqual(response["X-DjangoBridge-Action"], "close-overlay")
        content_type = PageContentType.objects.get(space=self.space, name="Recipe")
        self.assertEqual(content_type.field_count, 2)

    def test_an_invalid_schema_is_rejected(self):
        response = self.client.post(
            reverse("content_types_add", args=[self.space.slug]),
            {
                "name": "Broken",
                "schema": json.dumps(
                    {"fields": [{"name": "x", "type": "does_not_exist"}]}
                ),
            },
        )

        self.assertFalse(PageContentType.objects.exists())
        self.assertIn("schema", response.props["form"].errors)

    def test_duplicate_names_are_rejected(self):
        PageContentType.objects.create(
            space=self.space, name="Recipe", schema=BLOG_POST_SCHEMA
        )

        response = self.client.post(
            reverse("content_types_add", args=[self.space.slug]),
            {"name": "Recipe", "schema": json.dumps(BLOG_POST_SCHEMA)},
        )

        self.assertEqual(PageContentType.objects.count(), 1)
        self.assertIn("name", response.props["form"].errors)
