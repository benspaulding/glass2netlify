"""
Converts a Glass JSON export to a netlify-cms directory.

Accepts a file on the command line or stdin and writes to the current directory.
"""

import argparse
import datetime
import itertools
import pathlib
import sys
import traceback

import html2markdown
import yaml

from glass2netlify.req import iter_pages


def write_file(fobj, front, body):
    """
    Write out a SSG file.

       ---
       <YAML-serialized front matter>
       ---
       <body>
    """
    fobj.write("---\n")
    yaml.dump(front, stream=fobj)
    fobj.write("---\n")
    fobj.write(body)


def sort_heads_bodies(heads, bodies, mastheads={}):
    for n in itertools.count(1):
        b = bodies.get(f"Content_{n}" if n > 1 else "Content")
        h = heads.get(f"Subhead_{n}")
        m = mastheads.get(f"Masthead {n} CTA" if n > 1 else "Masthead CTA")
        if b is None and h is None:
            break

        yield h, b, m


def build_body(contents, tinfo):
    """
    Build up the body from the contents and template info.
    """
    # This is really based on templates/pages/home.html
    fields = tinfo["admin_fields"].get("fields", {})

    # Convert wysiwyg fields from HTML to MD
    for fname, fmeta in fields.items():
        if fmeta.get("type") == "wysiwyg" and fname in contents:
            contents[fname] = html2markdown.convert(contents[fname])

    # Pull out the content fields
    bodies = {
        k: contents.pop(k) for k in sorted(contents.keys()) if k.startswith("Content")
    }
    heads = {
        k: contents.pop(k) for k in sorted(contents.keys()) if k.startswith("Subhead")
    }
    masts = {
        k: contents.pop(k) for k in sorted(contents.keys()) if k.startswith("Masthead")
    }
    pairs = sort_heads_bodies(heads, bodies, masts)

    # Build contents
    # FIXME: Does not support CTA
    body = "".join(
        f"""
# {head}
{body}
"""
        if head
        else body
        for head, body, cta in pairs
    )
    return contents, body


CONVERSIONS = {
    "created": lambda v: datetime.datetime.fromisoformat(v) if v else v,
    "modified": lambda v: datetime.datetime.fromisoformat(v) if v else v,
    "published": lambda v: datetime.datetime.fromisoformat(v) if v else v,
    "last_published": lambda v: datetime.datetime.fromisoformat(v) if v else v,
}


def export_page(page, dest):
    """
    Export a single page to a destination directory.
    """

    for k, func in CONVERSIONS.items():
        if k in page:
            page[k] = func(page[k])

    contents = page.pop("content")
    template = page.pop("template_name")
    templ_info = page.pop("template")

    _ = page.pop("parent")
    _ = page.pop("is_parent")
    _ = page.pop("children")

    redirect = page.pop("redirect")
    assert not redirect, "redirect field not supported"

    lfunc = page.pop("lambda_func")
    assert not lfunc, "lambda_func not supported"

    path = page.pop("path")
    if not path:
        path = "index.md"
    else:
        path += ".md"
    path = dest / path

    page["content"], body = build_body(contents, templ_info)

    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("wt") as f:
        write_file(f, page, body)


def is_valid_file(parser, arg):
    p = pathlib.Path(arg)
    if arg == "-":
        return sys.stdin
    if p.is_file():
        return open(arg, "rt")
    else:
        parser.error(f"The file {arg!s} does not exist!")


def is_valid_directory(parser, arg):
    p = pathlib.Path(arg)
    if p.is_dir():
        return p.absolute()
    else:
        parser.error(f"{arg!s} is not a directory")


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "domain", default=sys.stdin, help="domain to pull from", metavar="NAME"
    )
    parser.add_argument(
        "--dest",
        default=pathlib.Path.cwd(),
        help="Destination directory",
        metavar="DIR",
        type=lambda x: is_valid_directory(parser, x),
    )
    return parser.parse_args()


def main():
    args = parse_args()
    dest = args.dest

    for page in iter_pages(args.domain):
        print(f"{page['path']}...")
        try:
            export_page(page, dest)
        except Exception:
            traceback.print_exc()
