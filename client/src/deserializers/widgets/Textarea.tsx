import { ReactElement } from "react";
import { WidgetDef } from "./base";
import Textarea from "../../components/widgets/Textarea";

export default class TextareaDef implements WidgetDef {
  rows: number;

  constructor(rows: number) {
    this.rows = rows;
  }

  render(
    id: string,
    name: string,
    disabled: boolean,
    value: string
  ): ReactElement {
    return (
      <Textarea
        id={id}
        name={name}
        disabled={disabled}
        defaultValue={value || ""}
        rows={this.rows}
      />
    );
  }
}
