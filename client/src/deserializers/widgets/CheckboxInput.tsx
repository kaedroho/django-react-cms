import { ReactElement } from "react";
import { WidgetDef } from "./base";
import CheckboxInput from "../../components/widgets/CheckboxInput";

export default class CheckboxInputDef implements WidgetDef {
  render(
    id: string,
    name: string,
    disabled: boolean,
    value: string
  ): ReactElement {
    // Django gives us the raw value; anything falsy means unchecked
    const checked = !!value && value !== "False" && value !== "false";

    return (
      <CheckboxInput
        id={id}
        name={name}
        disabled={disabled}
        defaultChecked={checked}
      />
    );
  }
}
