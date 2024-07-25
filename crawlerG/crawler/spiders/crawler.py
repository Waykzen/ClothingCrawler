import scrapy
from scrapy.crawler import CrawlerProcess
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
from urllib.parse import urlparse
import os
from collections import deque

class LinkSpider(CrawlSpider):
    name = "link_spider"

    def __init__(self, *args, **kwargs):
        super(LinkSpider, self).__init__(*args, **kwargs)
        self.start_urls = kwargs.get('start_urls', [])
        self.allowed_domains = [urlparse(url).netloc for url in self.start_urls]
        self.rules = (
            Rule(
                LinkExtractor(
                    allow_domains=self.allowed_domains,
                    deny=[
                        r'.*search.*', 
                        r'.*filter.*', 
                        r'.*sort.*', 
                        r'.*prefn1.*', 
                        r'.*prefv1.*', 
                        r'.*srule.*',   
                        r'.*pmin.*',
                        r'.*pmax.*',
                        r'.*img.*',
                        r'.*jobs.*',
                        r'.*pref.*',
                        r'.*ID.*',
                        r'.*[\?&]prefn1.*', 
                        r'.*[\?&]prefv1.*', 
                        r'.*[\?&]srule.*',
                        r'.*[\?&]pmin.*',
                        r'.*[\?&]pmax.*',
                        r'.*[\?&]searchColorID.*',
                        r'.*[\?&]size.*',
                        r'.*[\?&]sort.*'
                    ]  
                ), 
                callback='parse_item', 
                follow=True
            ),
        )
        self._compile_rules()
        self.visited_links = set()
        self.links_queue = deque()

    def parse_item(self, response):
        page_links = response.css('a::attr(href)').getall()
        
        for link in page_links:
            absolute_link = response.urljoin(link)
            if absolute_link not in self.visited_links:
                self.visited_links.add(absolute_link)
                self.links_queue.append(absolute_link)
                
                if len(self.links_queue) >= 1000:
                    self.write_links_to_file()

        for link in page_links:
            absolute_link = response.urljoin(link)
            if urlparse(absolute_link).netloc in self.allowed_domains:
                yield scrapy.Request(absolute_link, callback=self.parse_item)

    def write_links_to_file(self):
        filename = 'output_links.txt'
        filepath = os.path.join('/tmp', filename)
        with open(filepath, 'a') as f:
            while self.links_queue:
                f.write(self.links_queue.popleft() + "\n")

    def closed(self, reason):
        self.write_links_to_file()

def run_spider(urls):
    process = CrawlerProcess({
        'USER_AGENT': 'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1)'
    })

    process.crawl(LinkSpider, start_urls=urls)
    process.start()

if __name__ == "__main__":
    with open('urls.txt', 'r') as file:
        start_urls = [line.strip() for line in file.readlines()]
    run_spider(start_urls)
