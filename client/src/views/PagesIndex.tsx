import * as React from "react";
import PostAddIcon from "@mui/icons-material/PostAdd";
import Table from "@mui/joy/Table";
import Box from "@mui/joy/Box";
import Button from "@mui/joy/Button";
import Chip from "@mui/joy/Chip";
import IconButton from "@mui/joy/IconButton";
import Typography from "@mui/joy/Typography";
import Delete from "@mui/icons-material/Delete";
import HistoryIcon from "@mui/icons-material/History";
import DriveFileMoveIcon from "@mui/icons-material/DriveFileMove";
import ChevronRightIcon from "@mui/icons-material/ChevronRight";
import Link from "@mui/joy/Link";
import {
  Link as DjangoBridgeLink,
  NavigationContext,
} from "@django-bridge/react";

import Layout from "../components/Layout";
import ModalWindow from "../components/ModalWindow";
import StatusChip from "../components/StatusChip";
import { Crumb, Page } from "../types";

interface PagesIndexViewProps {
  parent: Page | null;
  parent_path: string;
  breadcrumb: Crumb[];
  pages: Page[];
  choose_content_type_url: string;
  content_types_index_url: string;
  has_content_types: boolean;
}

export default function PagesIndexView({
  parent,
  parent_path,
  breadcrumb,
  pages,
  choose_content_type_url,
  content_types_index_url,
  has_content_types,
}: PagesIndexViewProps) {
  const { openOverlay, refreshProps, navigate } =
    React.useContext(NavigationContext);

  const openInModal = React.useCallback(
    (url: string, slideout?: "left" | "right") =>
      openOverlay(
        url,
        (content) => <ModalWindow slideout={slideout}>{content}</ModalWindow>,
        { onClose: () => refreshProps() }
      ),
    [openOverlay, refreshProps]
  );

  // Each level of the tree is its own Django view and its own URL, so the
  // breadcrumb is just server-rendered links --- no client-side tree state.
  const crumbs = breadcrumb.map((crumb, i) => ({
    label: crumb.label,
    href: i === breadcrumb.length - 1 ? undefined : crumb.url,
  }));

  return (
    <Layout
      title={parent ? parent.title : "Pages"}
      subtitle={
        <Typography
          level="body-xs"
          sx={{ fontFamily: "monospace", mt: 0.25 }}
        >
          {parent_path}
        </Typography>
      }
      breadcrumb={crumbs}
      renderHeaderButtons={() => (
        <Box display="flex" gap={1} alignItems="center">
          {/* Buttons get their own onClick from MUI, which would clobber
              DjangoBridgeLink's --- so navigate explicitly instead. */}
          {parent && (
            <Button
              size="sm"
              variant="outlined"
              color="neutral"
              onClick={() => navigate(parent.edit_url)}
            >
              Edit this page
            </Button>
          )}
          <Button
            color="primary"
            startDecorator={<PostAddIcon />}
            size="sm"
            disabled={!has_content_types}
            onClick={() => openInModal(choose_content_type_url)}
          >
            Add child page
          </Button>
        </Box>
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
          <Typography level="body-md">
            {parent
              ? "This page has no children yet."
              : "No pages yet."}
          </Typography>
        </Box>
      )}

      {!!pages.length && (
        <Table
          sx={{
            // The page header above already supplies the one dividing line.
            // A filled table head would read as a second, competing band, so
            // the column labels carry themselves with type instead.
            "--TableCell-headBackground": "transparent",
            "& thead th": {
              fontSize: "11px",
              fontWeight: 600,
              letterSpacing: "0.06em",
              textTransform: "uppercase",
              color: "text.tertiary",
              verticalAlign: "middle",
            },
            "& tr > td:first-child": { paddingLeft: { xs: 2, md: 6 } },
            "& tr > th:first-child": { paddingLeft: { xs: 2, md: 6 } },
            "& tr > td:last-child": { paddingRight: { xs: 2, md: 6 } },
            "& tr > th:last-child": { paddingRight: { xs: 2, md: 6 } },
          }}
        >
          <thead>
            <tr>
              <th>Title</th>
              <th style={{ width: "14%" }}>Type</th>
              <th style={{ width: "11%" }}>Status</th>
              <th style={{ width: "10%" }}>Children</th>
              <th style={{ width: "11%" }}>Updated</th>
              <th style={{ width: "124px" }} aria-label="Actions" />
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
                    {page.path}
                  </Typography>
                </td>
                <td>
                  <Typography level="body-sm">{page.content_type}</Typography>
                </td>
                <td>
                  <StatusChip status={page.status} label={page.status_label} />
                </td>
                <td>
                  {/*
                    Always navigable, even at zero. This used to render an
                    em-dash for childless pages, which made them impossible to
                    browse into --- and therefore impossible to add a child to.
                  */}
                  <Link
                    component={DjangoBridgeLink}
                    href={page.children_url}
                    level="body-sm"
                    underline="none"
                    aria-label={`Open ${page.title}`}
                    sx={{ display: "inline-flex" }}
                  >
                    <Chip
                      size="sm"
                      variant={page.child_count ? "soft" : "outlined"}
                      color="neutral"
                      endDecorator={<ChevronRightIcon fontSize="small" />}
                    >
                      {page.child_count || "Open"}
                    </Chip>
                  </Link>
                </td>
                <td>
                  <Typography level="body-sm">{page.updated_at}</Typography>
                </td>
                <td>
                  <Box display="flex" gap={0.5}>
                    <IconButton
                      size="sm"
                      aria-label={`Move ${page.title}`}
                      onClick={() => openInModal(page.move_url)}
                    >
                      <DriveFileMoveIcon />
                    </IconButton>
                    <IconButton
                      size="sm"
                      aria-label={`History of ${page.title}`}
                      onClick={() => openInModal(page.revisions_url, "right")}
                    >
                      <HistoryIcon />
                    </IconButton>
                    <IconButton
                      size="sm"
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
