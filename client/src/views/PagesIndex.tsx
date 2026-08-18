import * as React from "react";
import PostAddIcon from "@mui/icons-material/PostAdd";
import Table from "@mui/joy/Table";
import Box from "@mui/joy/Box";
import Button from "@mui/joy/Button";
import IconButton from "@mui/joy/IconButton";
import Typography from "@mui/joy/Typography";
import Delete from "@mui/icons-material/Delete";
import HistoryIcon from "@mui/icons-material/History";
import Link from "@mui/joy/Link";
import {
  Link as DjangoBridgeLink,
  NavigationContext,
} from "@django-bridge/react";

import Layout from "../components/Layout";
import ModalWindow from "../components/ModalWindow";
import StatusChip from "../components/StatusChip";
import { Page } from "../types";

interface PagesIndexViewProps {
  pages: Page[];
  choose_content_type_url: string;
  content_types_index_url: string;
  has_content_types: boolean;
}

export default function PagesIndexView({
  pages,
  choose_content_type_url,
  content_types_index_url,
  has_content_types,
}: PagesIndexViewProps) {
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
      title="Pages"
      breadcrumb={[{ label: "" }]}
      renderHeaderButtons={() => (
        <Button
          color="primary"
          startDecorator={<PostAddIcon />}
          size="sm"
          disabled={!has_content_types}
          onClick={() => openInModal(choose_content_type_url)}
        >
          Add Page
        </Button>
      )}
      fullWidth
    >
      {!has_content_types && (
        <Box sx={{ px: { xs: 2, md: 6 }, py: 4 }}>
          <Typography level="body-md">
            There are no content types yet. A content type describes the fields
            a page has &mdash; define one and the page editor builds itself.{" "}
            <Link component={DjangoBridgeLink} href={content_types_index_url}>
              Create a content type
            </Link>
            .
          </Typography>
        </Box>
      )}

      {has_content_types && !pages.length && (
        <Box sx={{ px: { xs: 2, md: 6 }, py: 4 }}>
          <Typography level="body-md">No pages yet.</Typography>
        </Box>
      )}

      {!!pages.length && (
        <Table
          sx={{
            "& tr > td:first-child": { paddingLeft: { xs: 2, md: 6 } },
            "& tr > th:first-child": { paddingLeft: { xs: 2, md: 6 } },
            "& tr > td:last-child": { paddingRight: { xs: 2, md: 6 } },
            "& tr > th:last-child": { paddingRight: { xs: 2, md: 6 } },
          }}
        >
          <thead>
            <tr>
              <th>Title</th>
              <th style={{ width: "20%" }}>Type</th>
              <th style={{ width: "15%" }}>Status</th>
              <th style={{ width: "15%" }}>Updated</th>
              <th style={{ width: "110px" }} aria-label="Actions" />
            </tr>
          </thead>
          <tbody>
            {pages.map((page) => (
              <tr key={page.id}>
                <td>
                  <Link
                    component={DjangoBridgeLink}
                    level="title-md"
                    href={page.edit_url}
                  >
                    {page.title}
                  </Link>
                  <Typography level="body-xs" sx={{ fontFamily: "monospace" }}>
                    /{page.path}
                  </Typography>
                </td>
                <td>
                  <Typography level="body-sm">{page.content_type}</Typography>
                </td>
                <td>
                  <StatusChip status={page.status} label={page.status_label} />
                </td>
                <td>
                  <Typography level="body-sm">{page.updated_at}</Typography>
                </td>
                <td>
                  <Box display="flex" gap={0.5}>
                    <IconButton
                      size="sm"
                      aria-label={`History of ${page.title}`}
                      onClick={() => openInModal(page.revisions_url, "right")}
                    >
                      <HistoryIcon />
                    </IconButton>
                    <IconButton
                      size="sm"
                      color="danger"
                      aria-label={`Delete ${page.title}`}
                      onClick={() => openInModal(page.delete_url, "right")}
                    >
                      <Delete />
                    </IconButton>
                  </Box>
                </td>
              </tr>
            ))}
          </tbody>
        </Table>
      )}
    </Layout>
  );
}
