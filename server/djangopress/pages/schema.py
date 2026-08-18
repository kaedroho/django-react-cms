"""
Content type schemas.

A ``PageContentType`` stores a JSON schema describing the fields its pages
have. This module turns that JSON into a real Django ``Form`` class at
request time.

This is the bit that makes Django Bridge shine: the React client has no
knowledge of any content type. The server builds a form, telepath serialises
it, and the client renders whatever fields arrive. Adding a new field type is
one entry in ``FIELD_TYPES`` plus (occasionally) one React widget --- every
content type gets it for free, with no client-side schema protocol.

Schema format::

    {
        "title_field": "heading",
        "fields": [
            {"name": "heading", "type": "text", "label": "Heading",
             "required": true, "variant": "large"},
            {"name": "body", "type": "rich_text"},
            {"name": "published", "type": "boolean"}
        ]
    }
"""

import datetime
import json

from django import forms
from django.core.exceptions import ValidationError

from ..widgets import BlockNoteEditor


EMPTY_RICH_TEXT = [{"type": "paragraph", "content": ""}]


class FieldType:
    """
    Maps a schema field definition onto a Django form field, and converts
    values between the form's native Python type and the JSON stored in
    ``Page.content``.
    """

    #: Identifier used in the schema's ``type`` key.
    name = None
    #: Human readable name, shown in the content type editor.
    label = None
    #: Whether this field type can be used as a page's title field.
    can_be_title = False

    form_field_class = forms.CharField

    def get_widget(self, field_def):
        return None

    def get_kwargs(self, field_def):
        return {}

    def build_form_field(self, field_def):
        kwargs = {
            "label": field_def.get("label") or default_label(field_def["name"]),
            "required": field_def.get("required", False),
            "help_text": field_def.get("help_text", ""),
        }
        kwargs.update(self.get_kwargs(field_def))

        widget = self.get_widget(field_def)
        if widget is not None:
            kwargs["widget"] = widget

        return self.form_field_class(**kwargs)

    def to_json(self, value):
        """Convert a cleaned form value into something JSON serialisable."""
        return value

    def to_form(self, value):
        """Convert a value from ``Page.content`` back into a form initial."""
        return value

    def to_text(self, value):
        """A plain text representation, used for titles and search."""
        if value is None:
            return ""
        return str(value)


class TextFieldType(FieldType):
    name = "text"
    label = "Text"
    can_be_title = True

    def get_widget(self, field_def):
        attrs = {}
        if field_def.get("variant"):
            attrs["variant"] = field_def["variant"]
        return forms.TextInput(attrs=attrs)


class LongTextFieldType(FieldType):
    name = "long_text"
    label = "Long text"
    can_be_title = True

    def get_widget(self, field_def):
        return forms.Textarea(attrs={"rows": field_def.get("rows", 5)})


class RichTextFieldType(FieldType):
    name = "rich_text"
    label = "Rich text"

    def get_widget(self, field_def):
        return BlockNoteEditor()

    def get_kwargs(self, field_def):
        return {"initial": json.dumps(EMPTY_RICH_TEXT)}

    def to_json(self, value):
        # BlockNote posts back a JSON string. Store it as real JSON so the
        # content column stays queryable and readable.
        if not value:
            return EMPTY_RICH_TEXT
        if isinstance(value, str):
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return EMPTY_RICH_TEXT
        return value

    def to_form(self, value):
        if value is None:
            value = EMPTY_RICH_TEXT
        if isinstance(value, str):
            return value
        return json.dumps(value)

    def to_text(self, value):
        """Flatten BlockNote's document tree into plain text."""
        if isinstance(value, str):
            try:
                value = json.loads(value)
            except json.JSONDecodeError:
                return value

        def walk(nodes):
            for node in nodes or []:
                if isinstance(node, str):
                    yield node
                    continue
                if not isinstance(node, dict):
                    continue
                if node.get("type") == "text" and node.get("text"):
                    yield node["text"]
                yield from walk(node.get("content"))
                yield from walk(node.get("children"))

        return " ".join(part for part in walk(value) if part).strip()


class NumberFieldType(FieldType):
    name = "number"
    label = "Number"
    form_field_class = forms.FloatField

    def get_widget(self, field_def):
        return forms.NumberInput()

    def to_json(self, value):
        return value


class IntegerFieldType(NumberFieldType):
    name = "integer"
    label = "Whole number"
    form_field_class = forms.IntegerField


class BooleanFieldType(FieldType):
    name = "boolean"
    label = "Checkbox"
    form_field_class = forms.BooleanField

    def get_kwargs(self, field_def):
        # A checkbox that must be ticked is rarely what anyone means.
        return {"required": False}

    def to_json(self, value):
        return bool(value)


class DateFieldType(FieldType):
    name = "date"
    label = "Date"
    form_field_class = forms.DateField

    def get_widget(self, field_def):
        return forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d")

    def to_json(self, value):
        if isinstance(value, (datetime.date, datetime.datetime)):
            return value.isoformat()
        return value


class URLFieldType(FieldType):
    name = "url"
    label = "URL"
    form_field_class = forms.URLField

    def get_widget(self, field_def):
        return forms.URLInput()


class EmailFieldType(FieldType):
    name = "email"
    label = "Email address"
    form_field_class = forms.EmailField

    def get_widget(self, field_def):
        return forms.EmailInput()


class ChoiceFieldType(FieldType):
    name = "choice"
    label = "Dropdown"
    form_field_class = forms.ChoiceField
    can_be_title = True

    def get_kwargs(self, field_def):
        choices = []
        for choice in field_def.get("choices", []):
            if isinstance(choice, dict):
                choices.append((choice["value"], choice.get("label", choice["value"])))
            else:
                choices.append((choice, choice))

        if not field_def.get("required", False):
            choices.insert(0, ("", "---------"))

        return {"choices": choices}


FIELD_TYPES = {
    field_type.name: field_type()
    for field_type in [
        TextFieldType,
        LongTextFieldType,
        RichTextFieldType,
        NumberFieldType,
        IntegerFieldType,
        BooleanFieldType,
        DateFieldType,
        URLFieldType,
        EmailFieldType,
        ChoiceFieldType,
    ]
}


# Names the page editor uses for its own fields, so a content type can't
# claim them.
RESERVED_FIELD_NAMES = {"slug", "publish"}


def default_label(name):
    return name.replace("_", " ").capitalize()


def get_field_type(name):
    try:
        return FIELD_TYPES[name]
    except KeyError:
        raise ValidationError(f"Unknown field type: '{name}'")


def field_type_choices():
    """Used by the content type editor widget."""
    return [
        {
            "value": field_type.name,
            "label": field_type.label,
            "can_be_title": field_type.can_be_title,
        }
        for field_type in FIELD_TYPES.values()
    ]


def validate_schema(schema):
    """
    Raises ``ValidationError`` if the given schema is not usable.
    """
    if not isinstance(schema, dict):
        raise ValidationError("Schema must be an object.")

    fields = schema.get("fields")
    if not isinstance(fields, list) or not fields:
        raise ValidationError("Schema must define at least one field.")

    seen = set()
    for field_def in fields:
        if not isinstance(field_def, dict):
            raise ValidationError("Each field must be an object.")

        name = field_def.get("name")
        if not name or not isinstance(name, str):
            raise ValidationError("Every field needs a name.")
        if not name.isidentifier():
            raise ValidationError(
                f"'{name}' is not a valid field name. "
                "Use letters, numbers and underscores, and don't start with a number."
            )
        if name in seen:
            raise ValidationError(f"Duplicate field name: '{name}'")
        if name in RESERVED_FIELD_NAMES:
            raise ValidationError(
                f"'{name}' is reserved by the page editor. Pick another name."
            )
        seen.add(name)

        get_field_type(field_def.get("type"))

    title_field = schema.get("title_field")
    if title_field and title_field not in seen:
        raise ValidationError(
            f"title_field '{title_field}' does not match any field in the schema."
        )

    if not title_field and not any(
        get_field_type(f["type"]).can_be_title for f in fields
    ):
        raise ValidationError(
            "At least one field must be usable as a title "
            "(a text, long text or dropdown field)."
        )


def resolve_title_field(schema):
    """
    Returns the name of the field to use as the page title, falling back to
    the first field that could plausibly be one.
    """
    title_field = schema.get("title_field")
    if title_field:
        return title_field

    for field_def in schema.get("fields", []):
        try:
            if get_field_type(field_def.get("type")).can_be_title:
                return field_def["name"]
        except ValidationError:
            continue

    return None


def build_form_class(content_type, include_slug=False):
    """
    Builds a Django ``Form`` subclass from a content type's schema.

    The returned class is a completely ordinary form: it validates, it renders,
    and Django Bridge serialises it to the client like any other.

    ``include_slug`` appends the page editor's own slug field, which isn't part
    of the content type. It goes last so that content fields stay in schema
    order.
    """
    schema = content_type.schema
    attrs = {}

    for field_def in schema.get("fields", []):
        field_type = get_field_type(field_def.get("type"))
        attrs[field_def["name"]] = field_type.build_form_field(field_def)

    if include_slug:
        attrs["slug"] = forms.SlugField(
            label="Slug",
            required=False,
            help_text=(
                "The last segment of this page's URL. Changing it moves every "
                "page underneath it too. Leave blank to generate one from the "
                "title."
            ),
        )

    form_class = type(
        f"{content_type.name.title().replace(' ', '')}Form", (forms.Form,), attrs
    )
    form_class.schema = schema
    return form_class


def content_to_form_initial(content_type, content):
    """``Page.content`` -> form ``initial`` dict."""
    fields = (content or {}).get("fields", {})
    initial = {}

    for field_def in content_type.schema.get("fields", []):
        field_type = get_field_type(field_def.get("type"))
        initial[field_def["name"]] = field_type.to_form(fields.get(field_def["name"]))

    return initial


def cleaned_data_to_content(content_type, cleaned_data):
    """Cleaned form data -> the JSON stored in ``Page.content``."""
    fields = {}

    for field_def in content_type.schema.get("fields", []):
        field_type = get_field_type(field_def.get("type"))
        fields[field_def["name"]] = field_type.to_json(
            cleaned_data.get(field_def["name"])
        )

    return {"fields": fields}


def content_to_title(content_type, content):
    """Derive a page title from its content, using the schema's title field."""
    title_field = resolve_title_field(content_type.schema)
    if not title_field:
        return "Untitled"

    field_def = next(
        (f for f in content_type.schema["fields"] if f["name"] == title_field), None
    )
    if field_def is None:
        return "Untitled"

    value = (content or {}).get("fields", {}).get(title_field)
    return get_field_type(field_def["type"]).to_text(value).strip() or "Untitled"
