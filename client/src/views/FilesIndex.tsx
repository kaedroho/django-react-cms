import React from "react";
import styled from "styled-components";
import FileUploadIcon from '@mui/icons-material/FileUpload';
import Button from "@mui/joy/Button";

import Layout from "../components/Layout";
import { Link, MessagesContext, NavigationContext } from "@django-bridge/react";
import { CSRFTokenContext } from "../contexts";

const MAX_UPLOAD_SIZE = 4 * 1024 * 1024; // 4MB

function readFile(file: File): Promise<Uint8Array> {
  return new Promise((resolve) => {
    const reader = new FileReader();

    reader.onload = async (e) => {
      if (!e.target?.result) {
        return null;
      }

      resolve(new Uint8Array(e.target.result as ArrayBuffer));
    };

    reader.readAsArrayBuffer(file);
  });
}

async function uploadFile(
  file: File,
  uploadUrl: string,
  csrfToken: string,
){
  const fileData = await readFile(file);

  if (fileData.length > MAX_UPLOAD_SIZE) {
    throw "File size too large";
    return;
  }

  // Send file
  const formData = new FormData();
  formData.append("csrfmiddlewaretoken", csrfToken);
  formData.append("title", file.name);
  formData.append(
    "file",
    new Blob([fileData], {
      type: "application/octet-stream",
    }),
    file.name,
  );

  const response = await fetch(uploadUrl, {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    throw "Response from server was not OK";
  }
}

const FileListing = styled.ul`
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(125px, 1fr));
  grid-gap: 20px;
  list-style: none;
  margin: 20px;

  li {
    display: flex;
    flex-flow: column;
    align-items: center;
    justify-content: center;
  }

  figure {
    display: flex;
    flex-flow: column;
    align-items: center;
  }

  figcaption {
    margin-top: 10px;
  }
`;

interface FilesIndexViewProps {
  files: {
    id: number;
    name: string;
    edit_url: string;
  }[];
  upload_url: string;
}

export default function FilesIndexView({ files, upload_url }: FilesIndexViewProps) {
  const { refreshProps } = React.useContext(NavigationContext);
  const { pushMessage } = React.useContext(MessagesContext);
  const csrfToken = React.useContext(CSRFTokenContext);
  const fileInputRef = React.useRef<HTMLInputElement | null>(null);

  // A plain file input rather than showOpenFilePicker(). The File System
  // Access API is Chromium-only, and the ponyfill we used to call touches
  // FileSystemHandle at module scope, so merely importing this file threw
  // "FileSystemHandle is not defined" in Firefox and took the whole admin
  // down with it. Nothing here wants a file *handle* --- the next thing the
  // old code did was call getFile() --- so an <input type="file"> is both
  // simpler and universally supported.
  const handleFilesChosen = React.useCallback(
    async (event: React.ChangeEvent<HTMLInputElement>) => {
      const chosen = Array.from(event.target.files || []);

      // Reset so picking the same file again still fires a change event
      event.target.value = "";

      for (const file of chosen) {
        try {
          await uploadFile(file, upload_url, csrfToken);
        } catch {
          pushMessage({
            level: "error",
            text: `Couldn't upload ${file.name}.`,
          });
        }
      }

      if (chosen.length) {
        void refreshProps();
      }
    },
    [upload_url, csrfToken, refreshProps, pushMessage]
  );

  return (
    <Layout
      title="Media"
      breadcrumb={[{ label: "" }]}
      renderHeaderButtons={() => (
        <Button
          color="primary"
          startDecorator={<FileUploadIcon />}
          size="sm"
          onClick={() => fileInputRef.current?.click()}
        >
          Upload
        </Button>
      )}
    >
      <input
        ref={fileInputRef}
        type="file"
        multiple
        hidden
        onChange={handleFilesChosen}
      />

      <FileListing>
        {files.map((asset) => (
          <li key={asset.id}>
            <Link href={asset.edit_url}>
              <figure>
                {/* <img src={asset.thumbnail_url || "#"} alt={asset.title} /> */}
                <figcaption>{asset.name}</figcaption>
              </figure>
            </Link>
          </li>
        ))}
      </FileListing>
    </Layout>
  );
}
