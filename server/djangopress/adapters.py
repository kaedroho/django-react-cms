from django import forms
from django.conf import settings
from django.template.defaultfilters import filesizeformat
from django_bridge.adapters import Adapter, register

from .widgets import BlockNoteEditor, SchemaEditor


class TextInputAdapter(Adapter):
    js_constructor = "forms.TextInput"

    def js_args(self, widget):
        return [
            # Let the widget decide its own HTML input type. An explicit
            # `type` attr wins, which is how DateInput asks for a native date
            # picker.
            widget.attrs.get("type", getattr(widget, "input_type", "text")),
            widget.attrs.get("variant", "default"),
        ]


# Django's single-line input widgets are siblings, not subclasses of
# TextInput, so each needs registering. (DateInput and DateTimeInput *do*
# subclass TextInput, so they're covered.)
_text_input_adapter = TextInputAdapter()
for _widget_class in [
    forms.TextInput,
    forms.NumberInput,
    forms.EmailInput,
    forms.URLInput,
    forms.PasswordInput,
]:
    register(_text_input_adapter, _widget_class)


class TextareaAdapter(Adapter):
    js_constructor = "forms.Textarea"

    def js_args(self, widget):
        return [
            int(widget.attrs.get("rows", 5)),
        ]


register(TextareaAdapter(), forms.Textarea)


class CheckboxInputAdapter(Adapter):
    js_constructor = "forms.CheckboxInput"

    def js_args(self, widget):
        return []


register(CheckboxInputAdapter(), forms.CheckboxInput)


class FileInputAdapter(Adapter):
    js_constructor = "forms.FileInput"

    def js_args(self, widget):
        return [
            widget.attrs.get("class", ""),
            widget.attrs.get("accept", ""),
            filesizeformat(settings.MAX_UPLOAD_SIZE),
        ]


register(FileInputAdapter(), forms.FileInput)


class SelectAdapter(Adapter):
    js_constructor = "forms.Select"

    def js_args(self, widget):
        return [
            widget.options("__NAME__", ""),
            widget.attrs.get("class", ""),
        ]


register(SelectAdapter(), forms.Select)


class BlockNoteEditorAdapter(Adapter):
    js_constructor = "forms.BlockNoteEditor"

    def js_args(self, widget):
        return []


register(BlockNoteEditorAdapter(), BlockNoteEditor)


class SchemaEditorAdapter(Adapter):
    js_constructor = "forms.SchemaEditor"

    def js_args(self, widget):
        # The client gets the list of field types from the server, so adding a
        # field type in djangopress.pages.schema needs no frontend change.
        from .pages.schema import field_type_choices

        return [field_type_choices()]


register(SchemaEditorAdapter(), SchemaEditor)
