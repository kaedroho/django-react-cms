"""
Seeds a space with a few content types and pages.

A demo whose first screen is an empty list undersells everything, and a new
contributor running ``make setup`` should land on something they can poke at.
"""

from django.core.management.base import BaseCommand

from djangopress.pages import paths
from djangopress.pages.models import Page, PageContentType
from djangopress.spaces.models import Space


def rich_text(*paragraphs):
    return [
        {
            "id": f"p-{i}",
            "type": "paragraph",
            "props": {},
            "content": [{"type": "text", "text": text, "styles": {}}],
            "children": [],
        }
        for i, text in enumerate(paragraphs)
    ]


CONTENT_TYPES = {
    "Blog post": {
        "title_field": "title",
        "fields": [
            {
                "name": "title",
                "type": "text",
                "label": "Title",
                "required": True,
                "variant": "large",
            },
            {
                "name": "summary",
                "type": "long_text",
                "label": "Summary",
                "help_text": "Shown in listings and search results.",
            },
            {"name": "body", "type": "rich_text", "label": "Body"},
            {"name": "published_on", "type": "date", "label": "Published on"},
            {
                "name": "featured",
                "type": "boolean",
                "label": "Feature on the homepage",
            },
        ],
    },
    "Landing page": {
        "title_field": "heading",
        "fields": [
            {
                "name": "heading",
                "type": "text",
                "label": "Heading",
                "required": True,
                "variant": "large",
            },
            {"name": "intro", "type": "rich_text", "label": "Introduction"},
            {"name": "cta_label", "type": "text", "label": "Call to action label"},
            {"name": "cta_url", "type": "url", "label": "Call to action link"},
        ],
    },
    "Event": {
        "title_field": "name",
        "fields": [
            {
                "name": "name",
                "type": "text",
                "label": "Event name",
                "required": True,
                "variant": "large",
            },
            {"name": "starts_on", "type": "date", "label": "Starts on"},
            {"name": "location", "type": "text", "label": "Location"},
            {
                "name": "format",
                "type": "choice",
                "label": "Format",
                "choices": [
                    {"value": "in_person", "label": "In person"},
                    {"value": "online", "label": "Online"},
                    {"value": "hybrid", "label": "Hybrid"},
                ],
            },
            {"name": "capacity", "type": "integer", "label": "Capacity"},
            {"name": "details", "type": "rich_text", "label": "Details"},
        ],
    },
}


# (content type, parent path, slug, fields, publish)
PAGES = [
    (
        "Landing page",
        "/",
        "home",
        {
            "heading": "Djangopress",
            "intro": rich_text(
                "A small CMS built to show what Django Bridge is like to work with."
            ),
            "cta_label": "Read the docs",
            "cta_url": "https://django-bridge.org",
        },
        True,
    ),
    (
        "Landing page",
        "/",
        "blog",
        {
            "heading": "Blog",
            "intro": rich_text("Notes on building this thing."),
        },
        True,
    ),
    (
        "Blog post",
        "/blog/",
        None,
        {
            "title": "Why we built a CMS on Django Bridge",
            "summary": "No REST API, no GraphQL schema, no client-side form generator.",
            "body": rich_text(
                "Every content type in this CMS is a row in the database, not a "
                "Python class. The server builds a Django form from that row at "
                "request time and Django Bridge sends it to React.",
                "The React client has never heard of a 'Blog post'. It just "
                "renders the fields it is given.",
            ),
            "featured": True,
        },
        True,
    ),
    (
        "Blog post",
        "/blog/",
        None,
        {
            "title": "Drafts, revisions and publishing",
            "summary": "Two submit buttons on one plain Django form.",
            "body": rich_text(
                "Save draft and Publish are the same form posting to the same "
                "view. The branch is three lines of Python.",
                "This page has unpublished changes --- open it and compare the "
                "draft with what's live.",
            ),
        },
        "draft-over-live",
    ),
    (
        "Landing page",
        "/",
        "events",
        {
            "heading": "Events",
            "intro": rich_text("Where to find us."),
        },
        True,
    ),
    (
        "Event",
        "/events/",
        None,
        {
            "name": "Djangopress community call",
            "location": "Online",
            "format": "online",
            "capacity": 100,
            "details": rich_text("A monthly catch-up. Everyone welcome."),
        },
        False,
    ),
    (
        "Event",
        "/events/",
        None,
        {
            "name": "Sprint week",
            "location": "Bristol",
            "format": "hybrid",
            "capacity": 40,
            "details": rich_text("Five days of hacking on Django Bridge."),
        },
        True,
    ),
]


class Command(BaseCommand):
    help = "Create demo content types and pages in a space."

    def add_arguments(self, parser):
        parser.add_argument(
            "--space",
            help="Slug of the space to populate. Defaults to the first space.",
        )

    def handle(self, *args, **options):
        if options.get("space"):
            space = Space.objects.get(slug=options["space"])
        else:
            space = Space.objects.first()

        if space is None:
            self.stderr.write(
                "No spaces exist yet. Log in once to create one, then re-run this."
            )
            return

        content_types = {}
        for name, schema in CONTENT_TYPES.items():
            content_type, created = PageContentType.objects.get_or_create(
                space=space, name=name, version=1, defaults={"schema": schema}
            )
            if not created:
                content_type.schema = schema
                content_type.save(update_fields=["schema"])
            content_types[name] = content_type
            self.stdout.write(
                f"{'Created' if created else 'Updated'} content type: {name}"
            )

        for type_name, parent_path, slug, fields, publish in PAGES:
            content_type = content_types[type_name]

            page = Page(space=space, content_type=content_type, content={})
            page.update_content({"fields": fields})
            wanted = paths.join(parent_path, slug or paths.suggest_slug(page.title))

            if Page.objects.filter(space=space, path=wanted).exists():
                self.stdout.write(f"Skipping existing page: {wanted}")
                continue

            page.place_under(parent_path, slug=slug)
            page.save()
            page.save_revision()

            if publish:
                page.publish()

            if publish == "draft-over-live":
                # Publish, then leave an unpublished edit on top of it so the
                # "Live + draft" state is visible in the listing.
                fields = dict(fields, summary="Edited, but not published yet.")
                page.update_content({"fields": fields})
                page.save()
                page.save_revision()

            self.stdout.write(f"Created page: {page.path} ({page.status_label})")

        self.stdout.write(self.style.SUCCESS(f"Demo content ready in '{space.slug}'."))
