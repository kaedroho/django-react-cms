import * as React from "react";
import Button from "@mui/joy/Button";
import Box from "@mui/joy/Box";
import { Form, OverlayContext } from "@django-bridge/react";

import Layout from "../components/Layout";
import { CSRFTokenContext } from "../contexts";

interface ConfirmDeleteViewContext {
  objectName: string;
  messageHtml?: string;
  actionUrl: string;
  confirmLabel?: string;
}

function ConfirmDeleteView({
  objectName,
  messageHtml,
  actionUrl,
  confirmLabel,
}: ConfirmDeleteViewContext) {
  const { overlay, requestClose } = React.useContext(OverlayContext);
  const csrfToken = React.useContext(CSRFTokenContext);

  return (
    <Layout title={`${confirmLabel || "Delete"} ${objectName}`}>
      {messageHtml && (
        <Box
          sx={{ marginTop: "1rem" }}
          dangerouslySetInnerHTML={{ __html: messageHtml }}
        />
      )}

      <Form action={actionUrl} method="post">
        <input type="hidden" name="csrfmiddlewaretoken" value={csrfToken} />

        <Box display="flex" gap="12px" pt="20px">
          <Button type="submit" color="danger">
            {confirmLabel || "Delete"}
          </Button>
          {overlay && (
            <Button
              type="button"
              variant="outlined"
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
export default ConfirmDeleteView;
