import React from "react";
import JoyTextarea from "@mui/joy/Textarea";
import { DirtyFormMarker } from "@django-bridge/react";

interface TextareaProps {
  id: string;
  name: string;
  disabled: boolean;
  defaultValue: string;
  rows: number;
}

export default function Textarea({
  id,
  name,
  disabled,
  defaultValue,
  rows,
}: TextareaProps) {
  const [dirty, setDirty] = React.useState(false);

  return (
    <>
      {dirty && <DirtyFormMarker />}
      <JoyTextarea
        id={id}
        name={name}
        disabled={disabled}
        defaultValue={defaultValue}
        minRows={rows}
        onChange={() => setDirty(true)}
      />
    </>
  );
}
