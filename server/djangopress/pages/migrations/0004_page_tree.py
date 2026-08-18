from django.db import migrations, models


def slugs_to_paths(apps, schema_editor):
    """
    Before this migration `path` held a bare slug ("hello-world") and the tree
    was flat. Turn each one into a full path ("/hello-world/") at depth 1.
    """
    Page = apps.get_model("djangopress_pages", "Page")

    for page in Page.objects.all().iterator():
        slug = (page.slug or page.path or "").strip("/")
        if not slug:
            continue
        page.slug = slug
        page.path = f"/{slug}/"
        page.path_depth = 1
        page.save(update_fields=["slug", "path", "path_depth"])


def paths_to_slugs(apps, schema_editor):
    Page = apps.get_model("djangopress_pages", "Page")

    for page in Page.objects.all().iterator():
        page.path = page.path.strip("/").split("/")[-1]
        page.save(update_fields=["path"])


class Migration(migrations.Migration):

    dependencies = [
        ("djangopress_pages", "0003_publishing_and_revisions"),
        ("djangopress_spaces", "0002_alter_spaceuser_table"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="page",
            options={"ordering": ["path"]},
        ),
        migrations.AddField(
            model_name="page",
            name="path_depth",
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddIndex(
            model_name="page",
            index=models.Index(
                fields=["space", "path_depth"], name="djangopress_space_i_38fec8_idx"
            ),
        ),
        migrations.RunPython(slugs_to_paths, paths_to_slugs),
    ]
