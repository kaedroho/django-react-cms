import * as React from "react";
import Button from "@mui/joy/Button";
import Box from "@mui/joy/Box";
import Chip from "@mui/joy/Chip";
import Typography from "@mui/joy/Typography";
import HistoryIcon from "@mui/icons-material/History";
import DriveFileMoveIcon from "@mui/icons-material/DriveFileMove";
import ChevronRightIcon from "@mui/icons-material/ChevronRight";
import { Form, NavigationContext, OverlayContext } from "@django-bridge/react";

import FormDef from "../deserializers/Form";
import { Crumb, Page } from "../types";
import Layout from "../components/Layout";
import ModalWindow from "../components/ModalWindow";
import StatusChip from "../components/StatusChip";
import { CSRFTokenContext, URLsContext } from "../contexts";

interface PageFormViewProps {
  page: Page | null;
  parent_path: string | null;
  breadcrumb?: Crumb[];
  content_type: string;
  action_url: string;
  form: FormDef;
}

export default function PageFormView({
  page,
  parent_path,
  breadcrumb,
  content_type,
  action_url,
  form,
}: PageFormViewProps) {
  const { overlay, requestClose } = React.useContext(OverlayContext);
  const { openOverlay, refreshProps, navigate } =
    React.useContext(NavigationContext);
  const csrf_token = React.useContext(CSRFTokenContext);
  const urls = React.useContext(URLsContext);

  const openInModal = React.useCallback(
    (url: string, slideout?: "left" | "right") =>
      openOverlay(
        url,
        (content) => <ModalWindow slideout={slideout}>{content}</ModalWindow>,
        { onClose: () => refreshProps() }
      ),
    [openOverlay, refreshProps]
  );

  const crumbs = breadcrumb
    ? [...breadcrumb.map((c) => ({ label: c.label, href: c.url })), { label: "" }]
    : [{ label: "Pages", href: urls.pages_index }, { label: "" }];

  return (
    <Layout
      title={page ? page.title || "Untitled" : `New ${content_type}`}
      subtitle={
        <Box display="flex" gap={1} alignItems="center" sx={{ mt: 0.5 }}>
          <Chip size="sm" variant="soft" color="neutral">
            {content_type}
          </Chip>
          <Typography level="body-xs" sx={{ fontFamily: "monospace" }}>
            {page ? page.path : `${parent_path ?? "/"}\u2026`}
          </Typography>
        </Box>
      }
      breadcrumb={crumbs}
      renderHeaderButtons={
        page
          ? () => (
              <Box display="flex" gap={1} alignItems="center" flexWrap="wrap">
                <StatusChip status={page.status} label={page.status_label} />
                {!!page.child_count && (
                  <Button
                    size="sm"
                    variant="outlined"
                    color="neutral"
                    endDecorator={<ChevronRightIcon />}
                    onClick={() => navigate(page.children_url)}
                  >
                    {page.child_count} child
                    {page.child_count === 1 ? "" : "ren"}
                  </Button>
                )}
                <Button
                  size="sm"
                  variant="outlined"
                  color="neutral"
                  startDecorator={<DriveFileMoveIcon />}
                  onClick={() => openInModal(page.move_url)}
                >
                  Move
                </Button>
                <Button
                  size="sm"
                  variant="outlined"
                  color="neutral"
                  startDecorator={<HistoryIcon />}
                  onClick={() => openInModal(page.revisions_url, "right")}
                >
                  History
                </Button>
              </Box>
            )
          : undefined
      }
    >
      <Box sx={{ px: overlay ? 0 : { xs: 2, md: 6 }, pt: overlay ? 0 : 1 }}>
        <Form action={action_url} method="post">
          <input type="hidden" name="csrfmiddlewaretoken" value={csrf_token} />

          {form.render()}

          {/*
            Save draft and Publish are the same form posting to the same Django
            view. Django Bridge forwards the clicked button's name/value, so
            the view just checks `"publish" in request.POST`.
          */}
          <Box display="flex" gap="12px" pt="20px" flexWrap="wrap">
            <Button type="submit" variant="outlined" color="neutral">
              {page ? "Save draft" : "Save as draft"}
            </Button>
            <Button type="submit" name="publish" value="1" color="primary">
              {page && page.live ? "Publish changes" : "Publish"}
            </Button>
            {page && page.live && (
              <Button
                type="button"
                variant="plain"
                color="danger"
                onClick={() => openInModal(page.unpublish_url, "right")}
              >
                Unpublish
              </Button>
            )}
            {overlay && (
              <Button
                type="button"
                variant="plain"
                color="neutral"
                onClick={() => requestClose({ skipDirtyFormCheck: true })}
              >
                Cancel
              </Button>
            )}
          </Box>
        </Form>
      </Box>
    </Layout>
  );
}
