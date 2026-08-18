import React from "react";
import Box from "@mui/joy/Box";
import Button from "@mui/joy/Button";
import Checkbox from "@mui/joy/Checkbox";
import IconButton from "@mui/joy/IconButton";
import Input from "@mui/joy/Input";
import Option from "@mui/joy/Option";
import Select from "@mui/joy/Select";
import Sheet from "@mui/joy/Sheet";
import Typography from "@mui/joy/Typography";
import AddIcon from "@mui/icons-material/Add";
import DeleteIcon from "@mui/icons-material/Delete";
import ArrowUpwardIcon from "@mui/icons-material/ArrowUpward";
import ArrowDownwardIcon from "@mui/icons-material/ArrowDownward";
import { DirtyFormMarker } from "@django-bridge/react";

export interface FieldTypeChoice {
  value: string;
  label: string;
  can_be_title: boolean;
}

export interface SchemaField {
  name: string;
  type: string;
  label?: string;
  required?: boolean;
  variant?: string;
  help_text?: string;
}

export interface Schema {
  title_field?: string;
  fields: SchemaField[];
}

interface SchemaEditorProps {
  id: string;
  name: string;
  disabled: boolean;
  value: Schema;
  fieldTypes: FieldTypeChoice[];
}

function slugifyName(label: string) {
  return label
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "_")
    .replace(/^_+|_+$/g, "")
    .replace(/^([0-9])/, "field_$1");
}

/**
 * Edits the list of fields that make up a content type.
 *
 * The available field types come from the server (see `SchemaEditorAdapter`),
 * so adding a field type in `djangopress/pages/schema.py` makes it show up
 * here without touching this file.
 */
export default function SchemaEditor({
  name,
  disabled,
  value,
  fieldTypes,
}: SchemaEditorProps) {
  const [schema, setSchema] = React.useState<Schema>(
    value && Array.isArray(value.fields) ? value : { fields: [] }
  );
  const [dirty, setDirty] = React.useState(false);

  const update = React.useCallback((next: Schema) => {
    setSchema(next);
    setDirty(true);
  }, []);

  const titleCandidates = schema.fields.filter((field) =>
    fieldTypes.find((t) => t.value === field.type)?.can_be_title
  );

  const updateField = (index: number, changes: Partial<SchemaField>) => {
    const fields = schema.fields.map((field, i) =>
      i === index ? { ...field, ...changes } : field
    );
    update({ ...schema, fields });
  };

  const moveField = (index: number, delta: number) => {
    const target = index + delta;
    if (target < 0 || target >= schema.fields.length) {
      return;
    }
    const fields = [...schema.fields];
    [fields[index], fields[target]] = [fields[target], fields[index]];
    update({ ...schema, fields });
  };

  const removeField = (index: number) => {
    const removed = schema.fields[index];
    const fields = schema.fields.filter((_, i) => i !== index);
    update({
      ...schema,
      fields,
      title_field:
        schema.title_field === removed.name ? undefined : schema.title_field,
    });
  };

  const addField = () => {
    let suffix = schema.fields.length + 1;
    while (schema.fields.some((field) => field.name === `field_${suffix}`)) {
      suffix += 1;
    }
    update({
      ...schema,
      fields: [
        ...schema.fields,
        { name: `field_${suffix}`, label: "", type: "text", required: false },
      ],
    });
  };

  return (
    <>
      {dirty && <DirtyFormMarker />}
      {/* The form posts JSON; everything above is just a nicer way to edit it */}
      <input type="hidden" name={name} value={JSON.stringify(schema)} />

      <Box display="flex" flexDirection="column" gap={1}>
        {schema.fields.map((field, index) => (
          <Sheet
            key={index}
            variant="outlined"
            sx={{ p: 1.5, borderRadius: "sm", display: "flex", gap: 1 }}
          >
            <Box
              sx={{
                display: "grid",
                gridTemplateColumns: { xs: "1fr", sm: "2fr 2fr 1fr" },
                gap: 1,
                flex: 1,
              }}
            >
              <Input
                placeholder="Label"
                value={field.label ?? ""}
                disabled={disabled}
                onChange={(e) => {
                  const label = e.target.value;
                  const autoName =
                    !field.label ||
                    field.name === slugifyName(field.label) ||
                    /^field_\d+$/.test(field.name);
                  updateField(index, {
                    label,
                    ...(autoName ? { name: slugifyName(label) || field.name } : {}),
                  });
                }}
              />
              <Input
                placeholder="Name"
                value={field.name}
                disabled={disabled}
                onChange={(e) => updateField(index, { name: e.target.value })}
                sx={{ fontFamily: "monospace" }}
              />
              <Select
                value={field.type}
                disabled={disabled}
                onChange={(_, newType) =>
                  newType && updateField(index, { type: newType as string })
                }
              >
                {fieldTypes.map((fieldType) => (
                  <Option key={fieldType.value} value={fieldType.value}>
                    {fieldType.label}
                  </Option>
                ))}
              </Select>

              <Checkbox
                label="Required"
                size="sm"
                checked={!!field.required}
                disabled={disabled}
                onChange={(e) =>
                  updateField(index, { required: e.target.checked })
                }
              />
            </Box>

            <Box display="flex" flexDirection="column">
              <IconButton
                size="sm"
                disabled={disabled || index === 0}
                onClick={() => moveField(index, -1)}
                aria-label="Move up"
              >
                <ArrowUpwardIcon fontSize="small" />
              </IconButton>
              <IconButton
                size="sm"
                disabled={disabled || index === schema.fields.length - 1}
                onClick={() => moveField(index, 1)}
                aria-label="Move down"
              >
                <ArrowDownwardIcon fontSize="small" />
              </IconButton>
              <IconButton
                size="sm"
                color="danger"
                disabled={disabled}
                onClick={() => removeField(index)}
                aria-label="Remove field"
              >
                <DeleteIcon fontSize="small" />
              </IconButton>
            </Box>
          </Sheet>
        ))}

        <Box>
          <Button
            type="button"
            size="sm"
            variant="outlined"
            startDecorator={<AddIcon />}
            disabled={disabled}
            onClick={addField}
          >
            Add field
          </Button>
        </Box>

        <Box sx={{ pt: 1 }}>
          <Typography level="body-sm" sx={{ pb: 0.5 }}>
            Use as the page title
          </Typography>
          <Select
            value={schema.title_field ?? ""}
            disabled={disabled || !titleCandidates.length}
            onChange={(_, newValue) =>
              update({ ...schema, title_field: (newValue as string) || undefined })
            }
            placeholder="First suitable field"
          >
            <Option value="">First suitable field</Option>
            {titleCandidates.map((field) => (
              <Option key={field.name} value={field.name}>
                {field.label || field.name}
              </Option>
            ))}
          </Select>
        </Box>
      </Box>
    </>
  );
}
