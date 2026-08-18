import Chip from "@mui/joy/Chip";
import { PageStatus } from "../types";

const COLORS: Record<PageStatus, "success" | "warning" | "neutral"> = {
  live: "success",
  "live+draft": "warning",
  draft: "neutral",
  unpublished: "neutral",
};

interface StatusChipProps {
  status: PageStatus;
  label: string;
  size?: "sm" | "md" | "lg";
}

export default function StatusChip({ status, label, size }: StatusChipProps) {
  return (
    <Chip
      size={size || "sm"}
      variant="soft"
      color={COLORS[status] || "neutral"}
    >
      {label}
    </Chip>
  );
}
