import * as React from "react";
import Alert from "@mui/joy/Alert";
import Box from "@mui/joy/Box";
import Button from "@mui/joy/Button";
import Chip from "@mui/joy/Chip";
import List from "@mui/joy/List";
import ListItem from "@mui/joy/ListItem";
import ListItemButton from "@mui/joy/ListItemButton";
import ListItemContent from "@mui/joy/ListItemContent";
import Typography from "@mui/joy/Typography";
import { Form, OverlayContext } from "@django-bridge/react";

import Layout from "../components/Layout";
import { MoveCandidate, Page } from "../types";
import { CSRFTokenContext } from "../contexts";

interface MovePageViewProps {
  page: Page;
  descendant_count: number;
  candidates: MoveCandidate[];
  action_url: string;
  error: string | null;
}

/**
 * Pick a new parent for a page.
 *
 * The server has already filtered out the page's own subtree, since that's
 * the one destination a path-based tree can't represent.
 */
export default function MovePageView({
  page,
  descendant_count,
  candidates,
  action_url,
  error,
}: MovePageViewProps) {
  const csrfToken = React.useContext(CSRFTokenContext);
  const { requestClose } = React.useContext(OverlayContext);
  const [destination, setDestination] = React.useState<string | null>(null);

  return (
    <Layout title={`Move ${page.title}`}>
      {error && (
        <Alert color="danger" sx={{ mt: 2 }}>
          {error}
        </Alert>
      )}

      <Typography level="body-sm" sx={{ pt: 2 }}>
        Currently at <code>{page.path}</code>
        {descendant_count > 0 && (
          <>
            {" "}
            &mdash; {descendant_count} page
            {descendant_count === 1 ? "" : "s"} underneath will move with it and
            have their URLs rewritten.
          </>
        )}
      </Typography>

      <Form action={action_url} method="post" disableDirtyCheck>
        <input type="hidden" name="csrfmiddlewaretoken" value={csrfToken} />
        <input type="hidden" name="destination" value={destination ?? ""} />

        <List
          variant="outlined"
          sx={{ borderRadius: "sm", mt: 2, maxHeight: "50vh", overflow: "auto" }}
        >
          {candidates.map((candidate) => (
            <ListItem key={candidate.path}>
              <ListItemButton
                selected={destination === candidate.path}
                onClick={() => setDestination(candidate.path)}
                // Indent by depth so the shape of the tree is readable
                sx={{ pl: 2 + candidate.depth * 2 }}
              >
                <ListItemContent>
                  <Typography level="title-sm">{candidate.label}</Typography>
                  <Typography level="body-xs" sx={{ fontFamily: "monospace" }}>
                    {candidate.path}
                  </Typography>
                </ListItemContent>
                {candidate.current && (
                  <Chip size="sm" variant="soft">
                    Current parent
                  </Chip>
                )}
              </ListItemButton>
            </ListItem>
          ))}
        </List>

        {destination && (
          <Typography level="body-sm" sx={{ pt: 2 }}>
            New path: <code>{destination + page.slug + "/"}</code>
          </Typography>
        )}

        <Box display="flex" gap="12px" pt="20px">
          <Button type="submit" disabled={!destination}>
            Move page
          </Button>
          <Button
            type="button"
            variant="outlined"
            color="neutral"
            onClick={() => requestClose({ skipDirtyFormCheck: true })}
          >
            Cancel
          </Button>
        </Box>
      </Form>
    </Layout>
  );
}
