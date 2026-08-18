import * as React from "react";
import styled, { keyframes } from "styled-components";
import { CssVarsProvider } from "@mui/joy/styles";
import CssBaseline from "@mui/joy/CssBaseline";
import Box from "@mui/joy/Box";
import Breadcrumbs from "@mui/joy/Breadcrumbs";
import {
  DirtyFormContext,
  Link as DjangoBridgeLink,
  MessagesContext,
  OverlayContext,
} from "@django-bridge/react";
import Link from "@mui/joy/Link";
import Typography from "@mui/joy/Typography";
import WarningRounded from "@mui/icons-material/WarningRounded";

import HomeRoundedIcon from "@mui/icons-material/HomeRounded";
import ChevronRightRoundedIcon from "@mui/icons-material/ChevronRightRounded";

import Sidebar from "./Sidebar";
import Header from "./Header";
import Button from "@mui/joy/Button";
import { SxProps } from "@mui/joy/styles/types";

const slideDown = keyframes`
    from {
        margin-top: -50px;
    }

    to {
        margin-top: 0
    }
`;

const UnsavedChangesWarningWrapper = styled.div`
  display: flex;
  flex-flow: row nowrap;
  align-items: center;
  gap: 20px;
  padding: 15px 20px;
  color: #2e1f5e;
  font-size: 15px;
  font-weight: 400;
  margin-top: 0;
  background-color: #ffdadd;
  animation: ${slideDown} 0.5s ease;

  p {
    line-height: 19.5px;
  }

  strong {
    font-weight: 700;
  }
`;

interface LayoutProps {
  title: string;
  breadcrumb?: {
    label: string;
    href?: string;
  }[];
  renderHeaderButtons?: () => React.ReactNode;
  fullWidth?: boolean;
  hideHomeBreadcrumb?: boolean;
}

export default function Layout({
  title,
  breadcrumb = [],
  renderHeaderButtons,
  hideHomeBreadcrumb,
  children,
}: React.PropsWithChildren<LayoutProps>) {
  const { overlay } = React.useContext(OverlayContext);
  const { messages } = React.useContext(MessagesContext);
  const { unloadBlocked, confirmUnload } = React.useContext(DirtyFormContext);

  if (overlay) {
    // The view is being rendered in an overlay, no need to render the menus or base CSS
    return (
      <>
        {unloadBlocked && (
          <UnsavedChangesWarningWrapper role="alert" aria-live="assertive">
            <WarningRounded />
            <p>
              <strong>You have unsaved changes.</strong> Please save or cancel
              before closing
            </p>
          </UnsavedChangesWarningWrapper>
        )}
        <Box
          sx={{
            px: { xs: 2, md: 6 },
            pt: { xs: 2, sm: 2, md: 3 },
            pb: { xs: 2, sm: 2, md: 3 },
          }}
        >
          <Typography level="h3" component="h2">
            {title}
          </Typography>
          {renderHeaderButtons && renderHeaderButtons()}
          {children}
        </Box>
      </>
    );
  }

  return (
    <CssVarsProvider disableTransitionOnChange>
      <CssBaseline />
      <Box sx={{ display: "flex", minHeight: "100dvh", width: "100vw" }}>
        <Header />
        <Sidebar />
        <Box sx={{ display: "flex", flexFlow: "column nowrap", width: "100vw" }}>
          {unloadBlocked && (
            <UnsavedChangesWarningWrapper role="alert" aria-live="assertive">
              <WarningRounded />
              <p>
                <b>You have unsaved changes.</b> Please save your changes before
                leaving.
              </p>
              <Button
                type="button"
                size="sm"
                onClick={(e) => {
                  e.preventDefault();
                  confirmUnload();
                }}
              >
                Leave without saving
              </Button>
            </UnsavedChangesWarningWrapper>
          )}
          {!!messages.length && (
            <Box component="ul" sx={{ listStyleType: "none", p: 0, m: 0 }}>
              {messages.map((message) => {
                const sx: SxProps = {
                  px: 4,
                  py: 2,
                  color: "white",
                  fontWeight: 500,
                  backgroundColor: {
                    debug: "#4B5563",
                    info: "#2E5AAC",
                    success: "#1B8666",
                    warning: "#FAA500",
                    error: "#CA3B3B",
                  }[message.level],
                };
                if ("html" in message) {
                  return (
                    <Box
                      component="li"
                      sx={sx}
                      key={message.html}
                      role="alert"
                      aria-live={
                        message.level === "error" ? "assertive" : "polite"
                      }
                      dangerouslySetInnerHTML={{
                        __html: message.html,
                      }}
                    />
                  );
                }

                return (
                  <Box
                    component="li"
                    sx={sx}
                    key={message.text}
                    role="alert"
                    aria-live={
                      message.level === "error" ? "assertive" : "polite"
                    }
                  >
                    {message.text}
                  </Box>
                );
              })}
            </Box>
          )}
          <Box
            component="main"
            className="MainContent"
            sx={{
              pt: {
                xs: "calc(9px + var(--Header-height))",
                sm: "calc(9px + var(--Header-height))",
                md: 0,
              },
              pb: { xs: 2, sm: 2, md: 3 },
              flex: 1,
              display: "flex",
              flexDirection: "column",
              height: "100dvh",
              width: "calc(100vw - var(--Sidebar-width)",
              gap: 1,
            }}
          >
            <Box sx={{
              pb: 2,
              borderBottom: "1px solid var(--joy-palette-divider)"
            }}>
              <Box sx={{
                display: "flex",
                alignItems: "center",
              }}>
                <Breadcrumbs
                  size="sm"
                  aria-label="breadcrumbs"
                  separator={<ChevronRightRoundedIcon />}
                  sx={{ pl: 1, minHeight: "34px" }}
                >
                  {!hideHomeBreadcrumb && (
                    <Link
                      component={DjangoBridgeLink}
                      underline="none"
                      color="neutral"
                      href={"/"}
                      aria-label="Home"
                    >
                      <HomeRoundedIcon />
                    </Link>
                  )}
                  {breadcrumb.map(({ label, href }) =>
                    href ? (
                      <Link
                        component={DjangoBridgeLink}
                        underline="hover"
                        color="neutral"
                        href={href}
                        fontSize={12}
                        fontWeight={500}
                        key={href}
                      >
                        {label}
                      </Link>
                    ) : (
                      <Typography
                        color="primary"
                        fontWeight={500}
                        fontSize={12}
                      >
                        {label}
                      </Typography>
                    )
                  )}
                </Breadcrumbs>
              </Box>
              <Box
                sx={{
                  display: "flex",
                  mb: 1,
                  gap: 1,
                  flexDirection: { xs: "column", sm: "row" },
                  alignItems: { xs: "start", sm: "center" },
                  flexWrap: "wrap",
                  justifyContent: "space-between",
                  px: 2,
                }}
              >
                <Typography level="h3" component="h1">
                  {title}
                </Typography>
                {renderHeaderButtons && renderHeaderButtons()}
              </Box>
            </Box>
            {children}
          </Box>
        </Box>
      </Box>
    </CssVarsProvider>
  );
}
