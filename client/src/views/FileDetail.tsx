import * as React from "react";
import Layout from "../components/Layout";
import { URLsContext } from "../contexts";

interface FileDetailViewProps {
  title: string;
}

export default function FileDetailView({ title }: FileDetailViewProps) {
  const urls = React.useContext(URLsContext);

  return (
    <Layout
      title={title}
      breadcrumb={[{ label: "Media", href: urls.files_index }, { label: "" }]}
    />
  );
}
