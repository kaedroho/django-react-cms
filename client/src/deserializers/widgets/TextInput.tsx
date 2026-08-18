import { ReactElement } from "react";
import { WidgetDef } from "./base";
import TextInput from "../../components/widgets/TextInput";

export default class TextInputDef implements WidgetDef {
  // Whatever HTML input type the Django widget asked for. Django's
  // NumberInput/URLInput/EmailInput/DateInput all report their own, so they
  // work without needing a widget class of their own on this side.
  type: string;

  variant: "default" | "large";

  constructor(type: TextInputDef["type"], variant: TextInputDef["variant"]) {
    this.type = type;
    this.variant = variant;
  }

  render(
    id: string,
    name: string,
    disabled: boolean,
    value: string
  ): ReactElement {
    return (
      <TextInput
        id={id}
        type={this.type}
        avariant={this.variant}
        name={name}
        defaultValue={value}
        disabled={disabled}
      />
    );
  }
}
