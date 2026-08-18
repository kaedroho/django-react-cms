import * as React from "react";
import AddIcon from "@mui/icons-material/Add";
import Box from "@mui/joy/Box";
import Button from "@mui/joy/Button";
import Chip from "@mui/joy/Chip";
import IconButton from "@mui/joy/IconButton";
import Delete from "@mui/icons-material/Delete";
import Sheet from "@mui/joy/Sheet";
import Typography from "@mui/joy/Typography";
import { NavigationContext } from "@django-bridge/react";

import Layout from "../components/Layout";
import ModalWindow from "../components/ModalWindow";
import { ContentType } from "../types";

interface ContentTypesIndexViewProps {
  content_types: ContentType[];
  add_url: string;
}

export default function ContentTypesIndexView({
  content_types,
  add_url,
}: ContentTypesIndexViewProps) {
  const { openOverlay, refreshProps } = React.useContext(NavigationContext);

  const openInModal = React.useCallback(
    (url: string, slideout?: "left" | "right") =>
      openOverlay(
        url,
        (content) => <ModalWindow slideout={slideout}>{content}</ModalWindow>,
        { onClose: () => refreshProps() }
      ),
    [openOverlay, refreshProps]
  );

  return (
    <Layout
      title="Content types"
      breadcrumb={[{ label: "" }]}
      renderHeaderButtons={() => (
        <Button
          color="primary"
          size="sm"
          startDecorator={<AddIcon />}
          onClick={() => openInModal(add_url)}
        >
          Add content type
        </Button>
      )}
      fullWidth
    >
      <Box sx={{ px: { xs: 2, md: 6 }, pt: 2 }}>
        <Typography level="body-sm" sx={{ pb: 2, maxWidth: "60ch" }}>
          A content type describes the fields a page has. Editing one changes
          the page editor immediately &mdash; there's no Python class, no
          migration and no deploy behind any of this.
        </Typography>

        <Box display="flex" flexDirection="column" gap={1.5}>
          {content_types.map((contentType) => (
            <Sheet
              key={contentType.id}
              variant="outlined"
              sx={{ p: 2, borderRadius: "sm" }}
            >
              <Box
                display="flex"
                justifyContent="space-between"
                alignItems="flex-start"
                gap={1}
              >
                <Box>
                  <Typography level="title-md">{contentType.name}</Typography>
                  <Typography level="body-xs">
                    {contentType.page_count} page
                    {contentType.page_count === 1 ? "" : "s"}
                  </Typography>
                </Box>
                <Box display="flex" gap={0.5}>
                  <Button
                    size="sm"
                    variant="outlined"
                    color="neutral"
                    onClick={() => openInModal(contentType.edit_url)}
                  >
                    Edit fields
                  </Button>
                  <IconButton
                    size="sm"
                    aria-label={`Delete ${contentType.name}`}
                    onClick={() => openInModal(contentType.delete_url, "right")}
                  >
                    <Delete />
                  </IconButton>
                </Box>
              </Box>

              <Box display="flex" gap={0.5} flexWrap="wrap" pt={1.5}>
                {contentType.fields.map((field) => (
                  <Chip key={field.name} size="sm" variant="soft">
                    {field.label} &middot; {field.type}
                    {field.required ? " *" : ""}
                  </Chip>
                ))}
              </Box>
            </Sheet>
          ))}

          {!content_types.length && (
            <Typography level="body-md">
              No content types yet. Add one to start creating pages.
            </Typography>
          )}
        </Box>
      </Box>
    </Layout>
  );
}
