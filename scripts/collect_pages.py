#!/usr/bin/env python3
from mylog import mylog

from pathlib import Path
import requests
import re
from lxml.html import fromstring as lxsoup
from urllib.parse import parse_qs, urljoin, urlparse

MANUEL_INDEX_URL = 'https://www.osha.gov/pls/imis/sic_manual.html'
TARGET_DIR = Path('data', 'collected', 'sic_manual')


def page_path(url):
    """
    when url is MANUEL_INDEX_URL, returns: collected/sic_manual/index.html

    when url is a group url, e.g.
        'https://www.osha.gov/pls/imis/sic_manual.display?id=12&tab=group'
         returns: 'collected/sic_manual/group/12.html'

    when url is a detail/description page, e.g.
        'https://www.osha.gov/pls/imis/sic_manual.display?id=381&tab=description'
         returns: 'collected/sic_manual/description/381.html'
    """
    if url == MANUEL_INDEX_URL:
        return TARGET_DIR.joinpath('index.html')
    else:
        u = urlparse(url)
        q = parse_qs(u.query)
        tab = q['tab'][0]
        idstr = q['id'][0]
        if tab in ['group', 'description']:
            return TARGET_DIR.joinpath(tab, f'{idstr}.html')
        else:
            raise ValueError(f"Unexpected tab of: {tab}; {url}")



def fetch(url):
    """
    easy downloading function: provides progress bar
    https://stackoverflow.com/questions/37573483/progress-bar-while-download-file-over-http-with-requests
    """
    resp = requests.get(url)
    content_length = int(resp.headers.get('content-length', 0))
    blocksize = 1024
    progress_bar = tqdm(total=content_length, unit='iB', unit_scale=True)

    for datablock in resp.iter_content(blocksize):
        progress_bar.update(len(datablock))
        yield datablock
    progress_bar.close()


def fetch_and_save(url, target_path=None):
    """
    returns target_path when file has been freshly fetched or has otherwise been found
    """

    if target_path is None:
        target_path = page_path(url)

    def _existed_size(path):
        e = Path(path)
        if e.is_file():
            return e.stat().st_size
        else:
            return False

    def _save_file(content, target_path):
        target_path.parent.mkdir(exist_ok=True, parents=True)
        target_path.write_bytes(content)
        return target_path

    xb = _existed_size(target_path)

    if xb:
        mylog(f"{xb} bytes in {target_path}", label="Exists")
    else:
        mylog(url, label="Downloading")
        resp = requests.get(url)
        if resp.status_code == 200:
            _save_file(resp.content, target_path)
            mylog(target_path, f"{_existed_size(target_path)} bytes", label="Saved")

        else:
            print(resp.text)
            raise ValueError(f"Unexpected status code: `{resp.status_code}`")

    return target_path


def fetch_group_pages():
    def _read_manual():
        manual_srcpath = fetch_and_save(MANUEL_INDEX_URL)
        txt = manual_srcpath.read_bytes()
        return lxsoup(txt)

    def _get_group_urls():
        paths = _read_manual().xpath('//a[contains(@href, "&tab=group")]/@href')
        urls = [urljoin(MANUEL_INDEX_URL, p) for p in paths]
        return urls

    group_urls = _get_group_urls()

    mylog(f"Found {len(group_urls)} group urls")
    for i, url in enumerate(group_urls):
        mylog(f"({i+1}/{len(group_urls)}) {url}", label="Fetching")
        fetch_and_save(url)



def fetch_description_pages():
    def _get_group_paths():
        return sorted(TARGET_DIR.joinpath('group').glob('*.html'), key=lambda p: int(p.stem))

    def _get_desc_urls(srcpath):
        soup = lxsoup(srcpath.read_bytes())
        relpaths = soup.xpath('//a[contains(@href, "&tab=description")]/@href')
        urls = [urljoin(MANUEL_INDEX_URL, p) for p in relpaths]
        return urls

    srcpaths = _get_group_paths()
    mylog(f"Found {len(srcpaths)} group page files")

    for i, path in enumerate(srcpaths):
        mylog(f"({i+1}/{len(srcpaths)}) {path}", label="Souping")

        desc_urls = _get_desc_urls(path)
        mylog(f"Found {len(desc_urls)} description URLs")
        for j, url in enumerate(desc_urls):
            mylog(f"({j+1}/{len(desc_urls)}) {url}", label="Fetching")
            fetch_and_save(url)



def main():
    fetch_group_pages()
    fetch_description_pages()


if __name__ == '__main__':
    main()
