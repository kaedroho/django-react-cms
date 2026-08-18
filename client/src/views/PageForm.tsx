import * as React from "react";
import Button from "@mui/joy/Button";
import Box from "@mui/joy/Box";
import Typography from "@mui/joy/Typography";
import HistoryIcon from "@mui/icons-material/History";
import { Form, NavigationContext, OverlayContext } from "@django-bridge/react";

import FormDef from "../deserializers/Form";
import { Page } from "../types";
import Layout from "../components/Layout";
import ModalWindow from "../components/ModalWindow";
import StatusChip from "../components/StatusChip";
import { CSRFTokenContext, URLsContext } from "../contexts";

interface PageFormViewProps {
  page: Page | null;
  content_type: string;
  action_url: string;
  form: FormDef;
}

export default function PageFormView({
  page,
  content_type,
  action_url,
  form,
}: PageFormViewProps) {
  const { overlay, requestClose } = React.useContext(OverlayContext);
  const { openOverlay, refreshProps } = React.useContext(NavigationContext);
  const csrf_token = React.useContext(CSRFTokenContext);
  const urls = React.useContext(URLsContext);

  return (
    <Layout
      title={page ? page.title || "Untitled" : `New ${content_type}`}
      breadcrumb={[{ label: "Pages", href: urls.pages_index }, { label: "" }]}
      renderHeaderButtons={
        page
          ? () => (
              <Box display="flex" gap={1} alignItems="center">
                <StatusChip status={page.status} label={page.status_label} />
                <Button
                  size="sm"
                  variant="outlined"
                  color="neutral"
                  startDecorator={<HistoryIcon />}
                  onClick={() =>
                    openOverlay(
                      page.revisions_url,
                      (content) => (
                        <ModalWindow slideout="right">{content}</ModalWindow>
                      ),
                      { onClose: () => refreshProps() }
                    )
                  }
                >
                  History
                </Button>
              </Box>
            )
          : undefined
      }
    >
      <Box sx={{ px: overlay ? 0 : { xs: 2, md: 6 } }}>
        <Typography level="body-xs" sx={{ textTransform: "uppercase" }}>
          {content_type}
        </Typography>

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
                onClick={() =>
                  openOverlay(
                    page.unpublish_url,
                    (content) => (
                      <ModalWindow slideout="right">{content}</ModalWindow>
                    ),
                    { onClose: () => refreshProps() }
                  )
                }
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
