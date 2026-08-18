import * as React from "react";
import Box from "@mui/joy/Box";
import Button from "@mui/joy/Button";
import Chip from "@mui/joy/Chip";
import List from "@mui/joy/List";
import ListItem from "@mui/joy/ListItem";
import ListItemContent from "@mui/joy/ListItemContent";
import Typography from "@mui/joy/Typography";
import { Form, OverlayContext } from "@django-bridge/react";

import Layout from "../components/Layout";
import { Page, Revision } from "../types";
import { CSRFTokenContext } from "../contexts";

interface PageRevisionsViewProps {
  page: Page;
  revisions: Revision[];
}

export default function PageRevisionsView({
  page,
  revisions,
}: PageRevisionsViewProps) {
  const csrfToken = React.useContext(CSRFTokenContext);
  const { requestClose } = React.useContext(OverlayContext);

  return (
    <Layout title="History">
      <Typography level="body-sm">{page.title}</Typography>

      <List sx={{ pt: 2 }}>
        {revisions.map((revision) => (
          <ListItem key={revision.id} sx={{ alignItems: "flex-start" }}>
            <ListItemContent>
              <Box display="flex" gap={1} alignItems="center" flexWrap="wrap">
                <Typography level="title-sm">{revision.title}</Typography>
                {revision.is_live && (
                  <Chip size="sm" variant="soft" color="success">
                    Live
                  </Chip>
                )}
                {revision.is_latest && (
                  <Chip size="sm" variant="soft" color="neutral">
                    Latest draft
                  </Chip>
                )}
              </Box>
              <Typography level="body-xs">
                {revision.created_at} by {revision.created_by}
              </Typography>
            </ListItemContent>

            {!revision.is_latest && (
              <Form action={revision.revert_url} method="post" disableDirtyCheck>
                <input
                  type="hidden"
                  name="csrfmiddlewaretoken"
                  value={csrfToken}
                />
                <Button type="submit" size="sm" variant="outlined">
                  Restore
                </Button>
              </Form>
            )}
          </ListItem>
        ))}
      </List>

      <Box pt={2}>
        <Button
          type="button"
          variant="plain"
          color="neutral"
          onClick={() => requestClose({ skipDirtyFormCheck: true })}
        >
          Close
        </Button>
      </Box>
    </Layout>
  );
}
