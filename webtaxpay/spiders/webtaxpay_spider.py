import random
import re
from typing import Any, Iterable

import scrapy
from scrapy.http import Response
from scrapy.shell import inspect_response

PARCEL_IDS_FILENAME = 'parcel_ids.txt'
MAX_PARCEL_IDS = -1  # -1 = no limit
RANDOM_PARCEL_ID = False
STARTING_PARCEL_ID = None
START_URL = 'https://secure.webtaxpay.com/?county=yancey&state=NC'

LABEL_TO_SNAKE_RE = re.compile(r'[^a-z]+')


def label_to_snake(label: str) -> str:
    return LABEL_TO_SNAKE_RE.sub('_', label.lower()).strip('_')


class WebtaxpaySpider(scrapy.Spider):
    name = 'webtaxpay'
    start_urls = [START_URL]

    @staticmethod
    def get_parcel_ids() -> Iterable[str]:
        count = 0

        with open(PARCEL_IDS_FILENAME) as f:
            lines = f.readlines()

        if RANDOM_PARCEL_ID:
            random.shuffle(lines)
        lines = list(map(lambda l: l.strip(), filter(lambda l: l.strip(), lines)))
        if STARTING_PARCEL_ID:
            lines = lines[:lines.index(STARTING_PARCEL_ID)]

        for line in lines:
            if trimmed := line.strip():
                yield trimmed
            count += 1
            if MAX_PARCEL_IDS > 0 and count >= MAX_PARCEL_IDS:
                return

    def parse(self, response, **kwargs):
        for parcel_id in self.get_parcel_ids():
            yield scrapy.FormRequest.from_response(
                response=response,
                formdata={'search[search_by]': 'mapNo', 'search[search_by_string]': parcel_id, 'search[status]': 'All'},
                url='https://secure.webtaxpay.com/search.php',
                callback=self.parse_search_results,
            )

    def parse_search_results(self, response: Response, **kwargs):
        for button in response.xpath('//*[@id="hit_list"]//button'):
            yield scrapy.Request(url=f'https://secure.webtaxpay.com/taxcard.php?id={button.attrib['title']}&mobile=',
                                 callback=self.parse_card)

    def parse_card(self, response: Response, **kwargs):
        card = {}
        for tr in response.xpath("//table[@class and contains(concat(' ', normalize-space(@class), ' '), ' cardTable ')]//tr[td[@class and contains(concat(' ', normalize-space(@class), ' '), ' label ')]]"):
            label = tr.css('.label::text').get()
            value = tr.css('.value::text').get()
            if (
                    label == 'District:'
                    or 'city' in label.lower()
            ):
                continue
            card[label_to_snake(label)] = value
        yield card
