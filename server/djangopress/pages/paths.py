"""
Page paths.

A page's ``path`` is its full URL path within the space, and it is the page's
identity. ``path_depth`` is the number of segments in it.

    /                   depth 0   (the root of the space)
    /blog/              depth 1
    /blog/hello-world/  depth 2

Everything the tree needs falls out of those two columns:

    routing      path = "/blog/hello-world/"        exact match, one index hit
    children     path startswith "/blog/" and path_depth = 2
    descendants  path startswith "/blog/"
    siblings     same, using the parent path
    ancestors    path in ("/", "/blog/")            computed without a query
"""

from django.utils.text import slugify


ROOT_PATH = "/"


def normalise(path):
    """Coerce anything path-shaped into the canonical ``/a/b/`` form."""
    if not path:
        return ROOT_PATH

    segments = [segment for segment in str(path).split("/") if segment]
    if not segments:
        return ROOT_PATH

    return "/" + "/".join(segments) + "/"


def segments(path):
    return [segment for segment in normalise(path).split("/") if segment]


def depth(path):
    """Number of segments. The root is 0."""
    return len(segments(path))


def join(parent_path, slug):
    return normalise(parent_path) + slug.strip("/") + "/"


def parent_of(path):
    """The parent's path, or ``None`` if this is the root."""
    path = normalise(path)
    if path == ROOT_PATH:
        return None

    return "/" + "".join(f"{segment}/" for segment in segments(path)[:-1])


def slug_of(path):
    path_segments = segments(path)
    return path_segments[-1] if path_segments else ""


def ancestors_of(path, inclusive=False):
    """
    Every ancestor path, root first. No database access needed.

        /a/b/c/ -> ["/", "/a/", "/a/b/"]
    """
    result = [ROOT_PATH]
    current = ROOT_PATH

    for segment in segments(path)[:-1]:
        current = f"{current}{segment}/"
        result.append(current)

    if inclusive and normalise(path) != ROOT_PATH:
        result.append(normalise(path))

    return result


def is_descendant_of(path, ancestor_path):
    path = normalise(path)
    ancestor_path = normalise(ancestor_path)
    return path != ancestor_path and path.startswith(ancestor_path)


def suggest_slug(title):
    return slugify(title) or "page"
