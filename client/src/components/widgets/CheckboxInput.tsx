import React from "react";
import Checkbox from "@mui/joy/Checkbox";
import { DirtyFormMarker } from "@django-bridge/react";

interface CheckboxInputProps {
  id: string;
  name: string;
  disabled: boolean;
  defaultChecked: boolean;
}

export default function CheckboxInput({
  id,
  name,
  disabled,
  defaultChecked,
}: CheckboxInputProps) {
  const [dirty, setDirty] = React.useState(false);

  return (
    <>
      {dirty && <DirtyFormMarker />}
      <Checkbox
        id={id}
        name={name}
        value="on"
        disabled={disabled}
        defaultChecked={defaultChecked}
        onChange={() => setDirty(true)}
        sx={{ alignSelf: "flex-start" }}
      />
    </>
  );
}
