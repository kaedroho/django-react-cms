import { ReactElement } from "react";
import { WidgetDef } from "./base";
import SchemaEditor, {
  FieldTypeChoice,
  Schema,
} from "../../components/widgets/SchemaEditor";

export default class SchemaEditorDef implements WidgetDef {
  fieldTypes: FieldTypeChoice[];

  constructor(fieldTypes: FieldTypeChoice[]) {
    this.fieldTypes = fieldTypes;
  }

  render(
    id: string,
    name: string,
    disabled: boolean,
    value: string
  ): ReactElement {
    // Django's JSONField hands us the schema back as a JSON string
    let schema: Schema = { fields: [] };
    if (value) {
      try {
        schema = typeof value === "string" ? JSON.parse(value) : value;
      } catch {
        schema = { fields: [] };
      }
    }

    return (
      <SchemaEditor
        id={id}
        name={name}
        disabled={disabled}
        value={schema}
        fieldTypes={this.fieldTypes}
      />
    );
  }
}
