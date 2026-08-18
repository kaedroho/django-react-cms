import * as React from "react";
import Alert from "@mui/joy/Alert";
import Box from "@mui/joy/Box";
import Button from "@mui/joy/Button";
import { Form, OverlayContext } from "@django-bridge/react";

import FormDef from "../deserializers/Form";
import Layout from "../components/Layout";
import { ContentType } from "../types";
import { CSRFTokenContext } from "../contexts";

interface ContentTypeFormViewProps {
  content_type: ContentType | null;
  action_url: string;
  form: FormDef;
}

export default function ContentTypeFormView({
  content_type,
  action_url,
  form,
}: ContentTypeFormViewProps) {
  const { overlay, requestClose } = React.useContext(OverlayContext);
  const csrfToken = React.useContext(CSRFTokenContext);

  return (
    <Layout
      title={content_type ? `Editing ${content_type.name}` : "New content type"}
    >
      {!!content_type?.page_count && (
        <Alert color="warning" sx={{ mt: 2 }}>
          {content_type.page_count} existing page
          {content_type.page_count === 1 ? "" : "s"} use this content type.
          Removing a field hides its content; adding one leaves it empty on
          existing pages.
        </Alert>
      )}

      <Form action={action_url} method="post">
        <input type="hidden" name="csrfmiddlewaretoken" value={csrfToken} />

        {form.render()}

        <Box display="flex" gap="12px" pt="20px">
          <Button type="submit">
            {content_type ? "Save changes" : "Create content type"}
          </Button>
          {overlay && (
            <Button
              type="button"
              variant="outlined"
              color="neutral"
              onClick={() => requestClose({ skipDirtyFormCheck: true })}
            >
              Cancel
            </Button>
          )}
        </Box>
      </Form>
    </Layout>
  );
}
