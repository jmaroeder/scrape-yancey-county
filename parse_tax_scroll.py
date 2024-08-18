import json
import re
import sys
from random import random
from typing import Iterable

from pdfquery import PDFQuery
from pdfquery.cache import FileCache
from pyquery import PyQuery as pq

INPUT_PDF_FILE = 'YANCEY COUNTY TAX SCROLL 2024.pdf'
OUTPUT_JSON_FILE = 'scroll2024.json'
OUTPUT_SAMPLE = 0.01
# PAGES = list(range(0, 9))
# PAGES = [2, 9, 41]

REQUIRED_FIELDS = [
    'name',
    'address_line_1',
    'city',
    'state',
    'zip',
    'bill_number',
    'account_number',

    'pin',
    'size_a',
    'land_value',
    'building_value',
    'use_value',
    'equipment',
    'mobile_home',
    'vehicle',
    'other',
    'exclusion',
    'net_taxable',

    'county_tax',
    'fire',
    'district',
    'county_late',
    'deferred_tax',
    'total_due',

    'page',
]


def only_left_name():
    return float(this.get('x0')) < 37


def only_left_address():
    return float(this.get('x0')) < 309


def only_left_fire():
    return float(this.get('x0')) < 171


def parse_row(pdf: PDFQuery, pageid: int, y_offset: float):
    # y_offset is offset of PIN + 12.002
    return pdf.extract([
        ('with_parent', f'LTPage[pageid="{pageid}"]'),
        ('with_formatter', 'text'),

        ('name', f'LTTextLineHorizontal:in_bbox("36.482,{y_offset},309.086,{y_offset + 8.4}")',
         lambda match: match.filter(only_left_name).text()),
        # 171.343, 148.096, 229.89, 156.099
        ('address_line_1', f'LTTextLineHorizontal:in_bbox("171.343,{y_offset - 10},458.867,{y_offset + 8.4}")',
         lambda match: match.filter(only_left_address).text()),
        ('address_line_2', f'LTTextLineHorizontal:in_bbox("309.086,{y_offset},458.867,{y_offset + 8.4}")'),
        ('city', f'LTTextLineHorizontal:in_bbox("458.867,{y_offset},539.752,{y_offset + 8.4}")'),
        ('state', f'LTTextLineHorizontal:in_bbox("539.752,{y_offset},578.73,{y_offset + 8.4}")'),
        ('zip', f'LTTextLineHorizontal:in_bbox("578.73,{y_offset},669.596,{y_offset + 8.4}")'),
        ('bill_number', f'LTTextLineHorizontal:in_bbox("669.596,{y_offset},732.477,{y_offset + 8.4}")'),
        ('account_number', f'LTTextLineHorizontal:in_bbox("732.477,{y_offset},769.181,{y_offset + 8.4}")'),

        ('pin', f'LTTextLineHorizontal:in_bbox("36.482,{y_offset - 12.1},97.678,{y_offset - 12.1 + 8.4}")'),
        ('size_a', f'LTTextLineHorizontal:in_bbox("97.678,{y_offset - 12.1},171.343,{y_offset - 12.1 + 8.4}")'),
        ('land_value', f'LTTextLineHorizontal:in_bbox("171.343,{y_offset - 12.1},255.827,{y_offset - 12.1 + 8.4}")'),
        ('building_value',
         f'LTTextLineHorizontal:in_bbox("255.827,{y_offset - 12.1},356.999,{y_offset - 12.1 + 8.4}")'),
        ('use_value', f'LTTextLineHorizontal:in_bbox("356.999,{y_offset - 15.1},428.632,{y_offset - 15.1 + 8.4}")'),
        ('equipment', f'LTTextLineHorizontal:in_bbox("428.632,{y_offset - 12.1},487.459,{y_offset - 12.1 + 8.4}")'),
        ('mobile_home', f'LTTextLineHorizontal:in_bbox("487.459,{y_offset - 12.1},559.332,{y_offset - 12.1 + 8.4}")'),
        ('vehicle', f'LTTextLineHorizontal:in_bbox("559.332,{y_offset - 12.1},612.236,{y_offset - 12.1 + 8.4}")'),
        ('other', f'LTTextLineHorizontal:in_bbox("612.236,{y_offset - 12.1},660.739,{y_offset - 12.1 + 8.4}")'),
        ('exclusion', f'LTTextLineHorizontal:in_bbox("631.645,{y_offset - 12.1},732.477,{y_offset - 12.1 + 8.4}")'),
        ('net_taxable', f'LTTextLineHorizontal:in_bbox("706.301,{y_offset - 12.1},769.181,{y_offset - 12.1 + 8.4}")'),

        ('county_tax',
         f'LTTextLineHorizontal:in_bbox("36.482,{y_offset - 12.1 * 2},97.678,{y_offset - 12.1 * 2 + 8.4}")'),
        ('fire', f'LTTextLineHorizontal:in_bbox("97.678,{y_offset - 12.1 * 2},255.827,{y_offset - 12.1 * 2 + 8.4}")',
         lambda match: match.filter(only_left_fire).text()),
        ('district',
         f'LTTextLineHorizontal:in_bbox("171.343,{y_offset - 12.1 * 2},309.086,{y_offset - 12.1 * 2 + 8.4}")'),
        ('county_late',
         f'LTTextLineHorizontal:in_bbox("309.086,{y_offset - 12.1 * 2},458.867,{y_offset - 12.1 * 2 + 8.4}")'),
        ('deferred_tax',
         f'LTTextLineHorizontal:in_bbox("612.236,{y_offset - 12.1 * 2 - 3},706.301,{y_offset - 12.1 * 2 - 3 + 8.4}")'),
        ('total_due',
         f'LTTextLineHorizontal:in_bbox("706.301,{y_offset - 12.1 * 2},769.181,{y_offset - 12.1 * 2 + 8.4}")'),

        ('page', 'LTTextLineHorizontal:in_bbox("396,33.29,792,44.295")',
         lambda match: int(re.search(r'Page (\d+) of \d+', match.text(), re.IGNORECASE).group(1))),
    ])


def is_pin():
    t: str = pq(this).text()
    return len(t) == 15 and t.isdigit()


def parse_page(pdf: PDFQuery, pageid: int) -> Iterable[dict[str, str]]:
    for pin in pdf.pq(f'LTPage[pageid="{pageid}"] LTTextLineHorizontal').filter(is_pin):
        yield parse_row(pdf, pageid, float(pin.get('y0')) + 11.9)


def parse_pdf():
    pdf = PDFQuery(INPUT_PDF_FILE, parse_tree_cacher=FileCache('/tmp/'))
    pdf.load()
    # pdf.load(list(range(0, 5)))
    # pdf.load(PAGES)

    for ltpage in pdf.pq('LTPage'):
        pageid = int(ltpage.get('pageid'))
        for result in parse_page(pdf, pageid):
            if result['name'] and not result['address_line_1']:
                if match := re.search(r' (\d+ .+|PO BOX .*|C/O .*)', result['name'], re.IGNORECASE):
                    result['name'] = result['name'][:match.start()]
                    result['address_line_1'] = match.group(1)

            if result['address_line_2'] and not result['address_line_1']:
                result['address_line_1'] = result['address_line_2']
                result['address_line_2'] = ''

            if '\n' in result['fire']:
                result['fire'] = result['fire'].split('\n', 1)[0]

            if not result['district'] and ' ' in result['fire']:
                result['fire'], result['district'] = result['fire'].split(' ', 1)

            if not result['land_value'] and result['size_a'] == "0":
                result['land_value'] = "$0.00"

            missing_fields = set()
            for required_field in REQUIRED_FIELDS:
                if not result[required_field]:
                    missing_fields.add(required_field)
            if not len(missing_fields) == 0:
                print(
                    f'Missing fields for pin {result['pin']} on page {result['page'] or pageid}: {','.join(missing_fields)}',
                    file=sys.stderr)
            yield result


if __name__ == '__main__':
    result = []
    for row in parse_pdf():
        result.append(row)
        if random() < OUTPUT_SAMPLE:
            print(json.dumps(row))
    with open(OUTPUT_JSON_FILE, 'w') as f:
        json.dump(result, f, indent=2)
