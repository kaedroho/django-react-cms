from django.forms import TextInput, Widget


class BlockNoteEditor(TextInput):
    pass


class SchemaEditor(Widget):
    """
    Edits a content type's field list.

    The list of available field types is supplied by the server (see
    ``SchemaEditorAdapter``), so adding a new field type in
    ``djangopress.pages.schema`` makes it appear in this editor without any
    frontend change at all.
    """

    pass
