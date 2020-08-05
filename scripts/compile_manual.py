#!/usr/bin/env python3
import csv
from mylog import mylog
from pathlib import Path
import re
from lxml.html import fromstring as lxsoup

SRC_DIR = Path('data', 'collected', 'sic_manual', 'description',)
TARGET_PATH = Path('data', 'compiled', 'sic_manual.csv')

COMPILED_HEADERS = (
    'sic_code', 'sic_name',
    'group_code', 'group_name',
    'division_code', 'division_name',
    'url',
    'sic_description',
    'sic_examples',
)

def parse_description_page(txt):
    _rx_division = r'Division ([A-Z]): (.+)'
    def _extract_division(soup):
        dtext = next(t for t in soup.xpath('//a[contains(@title, "Division")]/@title') if re.match(_rx_division, t))
        return re.match(_rx_division, dtext).groups()

    _rx_group = r'Major Group (\d+): (.+)'
    def _extract_group(soup):
        dtext = next(t for t in soup.xpath('//a[contains(@title, "Major Group")]/@title') if re.match(_rx_group, t))
        return re.match(_rx_group, dtext).groups()

    _rx_sic= r'Description for (\d{4}): (.+)'
    def _extract_sic(soup):
        # try:
        # except StopIteration:
        #     import pdb; pdb.set_trace()
        dtext = next(t for t in soup.xpath('//h2[contains(text(), "Description")]/text()') if re.match(_rx_sic, t))
        return re.match(_rx_sic, dtext).groups()

    def _extract_sic_desc(soup):
        els = soup.xpath('//span[contains(@class, "blueTen")]/text()')
        if len(els) == 0:
            return ""
        elif len(els) > 1:
            import pdb; pdb.set_trace()
        else:
            return els[0]

    def _extract_sic_examples(soup):
        examples = soup.xpath('//span[contains(@class, "blueTen")]/following-sibling::ul[1]/li/text()')
        if len(examples) == 0:
            return ""
        else:
            return '\n'.join(e.strip() for e in examples)


    soup = lxsoup(txt)
    d = {}
    d['division_code'], d['division_name'] = _extract_division(soup)
    d['group_code'], d['group_name'] = _extract_group(soup)
    d['sic_code'], d['sic_name'] = _extract_sic(soup)
    d['sic_description'] = _extract_sic_desc(soup)
    d['sic_examples'] = _extract_sic_examples(soup)
    return d

def make_desc_page_url(page_path):
    idstr = page_path.stem
    return f"https://www.osha.gov/pls/imis/sic_manual.display?id={idstr}&tab=description"


def main():
    def _get_desc_paths():
        return sorted(SRC_DIR.glob('*.html'), key=lambda p: int(p.stem))

    def _read_text(path):
        return path.read_bytes().decode('latin-1')

    srcpaths = _get_desc_paths()
    mylog(f"{len(srcpaths)} files in {SRC_DIR}", label="Gathered")

    TARGET_PATH.parent.mkdir(exist_ok=True, parents=True)
    with open(TARGET_PATH, 'w') as target_file:
        mylog(TARGET_PATH, label="Writing to")
        target = csv.DictWriter(target_file, fieldnames=COMPILED_HEADERS)
        target.writeheader()


        for i, srcpath in enumerate(srcpaths):
            txt = _read_text(srcpath)
            record = parse_description_page(txt)
            record['url'] = make_desc_page_url(srcpath)

            target.writerow(record)
            if i % 50 == 0:
                mylog(f"{i} out of {len(srcpaths)} – {srcpath}" ,label="Parsing")


if __name__ == '__main__':
    main()
