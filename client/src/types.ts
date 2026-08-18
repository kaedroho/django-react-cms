export type PageStatus = "draft" | "live" | "live+draft" | "unpublished";

export interface Page {
  id: string;
  title: string;
  /** Full URL path within the space, e.g. "/blog/hello-world/". */
  path: string;
  slug: string;
  /** Number of segments in `path`. The root is 0. */
  depth: number;
  content_type: string;
  status: PageStatus;
  status_label: string;
  live: boolean;
  has_unpublished_changes: boolean;
  updated_at: string;
  child_count: number | null;
  children_url: string;
  edit_url: string;
  delete_url: string;
  move_url: string;
  revisions_url: string;
  unpublish_url: string;
}

export interface Crumb {
  label: string;
  path: string;
  url: string;
}

export interface MoveCandidate {
  path: string;
  label: string;
  depth: number;
  current: boolean;
}

export interface ContentTypeField {
  name: string;
  label: string;
  type: string;
  required: boolean;
}

export interface ContentType {
  id: number;
  name: string;
  field_count: number;
  page_count: number;
  fields: ContentTypeField[];
  edit_url: string;
  delete_url: string;
}

export interface Revision {
  id: string;
  title: string;
  created_at: string;
  created_by: string;
  is_live: boolean;
  is_latest: boolean;
  revert_url: string;
}
