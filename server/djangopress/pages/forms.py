from django import forms
from django.core.exceptions import ValidationError

from .models import PageContentType
from .schema import validate_schema
from ..widgets import SchemaEditor


class ContentTypeForm(forms.ModelForm):
    """
    A form for editing the *definition* of a content type.

    Saving this form changes what fields the page editor shows --- no Python
    change, no migration, no deploy.
    """

    name = forms.CharField(
        label="Name",
        help_text="What editors see when choosing what kind of page to create.",
    )
    schema = forms.JSONField(
        label="Fields",
        widget=SchemaEditor(),
        initial={
            "fields": [
                {"name": "title", "type": "text", "required": True, "variant": "large"}
            ]
        },
    )

    class Meta:
        model = PageContentType
        fields = ["name", "schema"]

    def __init__(self, *args, space=None, **kwargs):
        self.space = space
        super().__init__(*args, **kwargs)

    def clean_schema(self):
        schema = self.cleaned_data["schema"]
        validate_schema(schema)
        return schema

    def clean_name(self):
        name = self.cleaned_data["name"].strip()

        if self.space is not None:
            clash = PageContentType.objects.filter(space=self.space, name=name)
            if self.instance.pk:
                clash = clash.exclude(pk=self.instance.pk)
            if clash.exists():
                raise ValidationError(
                    f"A content type named '{name}' already exists in this space."
                )

        return name
