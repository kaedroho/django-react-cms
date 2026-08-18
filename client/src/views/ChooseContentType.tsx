import * as React from "react";
import Box from "@mui/joy/Box";
import Link from "@mui/joy/Link";
import List from "@mui/joy/List";
import ListItem from "@mui/joy/ListItem";
import ListItemButton from "@mui/joy/ListItemButton";
import ListItemContent from "@mui/joy/ListItemContent";
import Typography from "@mui/joy/Typography";
import ChevronRightIcon from "@mui/icons-material/ChevronRight";
import {
  Link as DjangoBridgeLink,
  NavigationContext,
} from "@django-bridge/react";

import Layout from "../components/Layout";

interface ChooseContentTypeViewProps {
  content_types: {
    id: number;
    name: string;
    field_count: number;
    add_url: string;
  }[];
  content_types_add_url: string;
}

/**
 * Step one of adding a page.
 *
 * Picking a type navigates *within the overlay* to the add form, which keeps
 * the whole flow inside a single overlay (Django Bridge doesn't support
 * nesting them).
 */
export default function ChooseContentTypeView({
  content_types,
  content_types_add_url,
}: ChooseContentTypeViewProps) {
  // Note: don't use `component={DjangoBridgeLink}` on ListItemButton. MUI
  // passes its own onClick, and Django Bridge's buildLinkElement spreads
  // incoming props *after* its handler --- so the navigation handler is
  // silently replaced and the browser does a full page load instead.
  const { navigate } = React.useContext(NavigationContext);

  return (
    <Layout title="What kind of page?">
      <Box sx={{ pt: 2 }}>
        <List variant="outlined" sx={{ borderRadius: "sm" }}>
          {content_types.map((contentType) => (
            <ListItem key={contentType.id}>
              <ListItemButton onClick={() => navigate(contentType.add_url)}>
                <ListItemContent>
                  <Typography level="title-sm">{contentType.name}</Typography>
                  <Typography level="body-xs">
                    {contentType.field_count} field
                    {contentType.field_count === 1 ? "" : "s"}
                  </Typography>
                </ListItemContent>
                <ChevronRightIcon />
              </ListItemButton>
            </ListItem>
          ))}
        </List>

        <Typography level="body-sm" sx={{ pt: 2 }}>
          Need something else?{" "}
          <Link component={DjangoBridgeLink} href={content_types_add_url}>
            Define a new content type
          </Link>{" "}
          &mdash; no deploy required.
        </Typography>
      </Box>
    </Layout>
  );
}
