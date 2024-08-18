from typing import Any

import scrapy
from scrapy.http import Response


class Spider(scrapy.Spider):
    name = 'yanceyassessorspider'
    start_urls = ['https://secure.webtaxpay.com/?county=yancey&state=NC']

    def parse(self, response: Response):
        pass