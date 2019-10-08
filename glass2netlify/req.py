"""
Handles the API
"""

import collections
from pprint import pprint

import requests


def http_session():
    _user = "jamie@lumami.biz"  # input("User: ")
    _pass = "admin345^"  # input("Pass: ")
    s = requests.Session()
    s.auth = (_user, _pass)
    return s


def iter_pages(domain):
    http = http_session()

    resp = http.get(f"http://{domain}/siteapi/pages.json")
    resp.raise_for_status()
    pages = collections.deque(resp.json())

    while pages:
        page = pages.popleft()

        if 'path' not in page:
            pprint(page)

        yield page.copy()

        for child in page.get('children', []):
            resp = http.get(f"http://{domain}/{child['path']}.json")
            resp.raise_for_status()
            cdata = resp.json()
            assert cdata['path'] == child['path']
            assert cdata['parent']  # == ???
            pages.append(cdata)

    assert not pages
