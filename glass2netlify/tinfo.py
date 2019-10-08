"""
Spit out information on templates.
"""
import argparse
import json
import sys

from glass2netlify.req import iter_pages


templates = []


def add(templ):
    for t in templates:
        if t == templ:
            break
    else:
        templates.append(templ)


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("domain", default=sys.stdin,
                        help="domain to pull from", metavar="NAME")
    return parser.parse_args()


def main():
    args = parse_args()
    for page in iter_pages(args.domain):
        add(page['template'])
    json.dump(
        sorted(templates, key=lambda v: v['path']),
        sys.stdout, indent=True,
    )


if __name__ == '__main__':
    sys.exit(main())
