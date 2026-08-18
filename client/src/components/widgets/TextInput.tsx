import InputProps from "@mui/joy/Input/InputProps";
import { SxProps } from "@mui/joy/styles/types";
import Input from "@mui/joy/Input";
import { DirtyFormMarker } from "@django-bridge/react";
import React from "react";

export interface TextInputProps extends InputProps {
  avariant: "default" | "large";
}

export default function TextInput({
  avariant,
  onChange: originalOnChange,
  ...props
}: TextInputProps) {
  const [dirty, setDirty] = React.useState(false);

  let sx: SxProps = props.sx || {};
  if (avariant === "large") {
    sx = {
      ...sx,
      // Big type, but still visibly a field: a hairline edge that firms up on
      // hover and focus. Fully borderless left people unsure it was editable,
      // and it didn't line up with the inputs below it.
      "--Input-minHeight": "auto",
      border: "1px solid",
      borderColor: "neutral.outlinedBorder",
      boxShadow: "none",
      background: "none",
      fontSize: { xs: "28px", sm: "32px", md: "40px" },
      fontWeight: 700,
      lineHeight: 1.2,
      py: 1,
      "&:hover": { borderColor: "neutral.outlinedHoverBorder" },
      "&:focus-within": {
        borderColor: "primary.outlinedBorder",
      },
    };
  }

  const onChange = React.useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      setDirty(true);

      if (originalOnChange) {
        originalOnChange(e);
      }
    },
    [originalOnChange]
  );

  return (
    <>
      {dirty && <DirtyFormMarker />}
      <Input {...props} sx={sx} onChange={onChange} />
    </>
  );
}
