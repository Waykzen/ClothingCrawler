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
        self.current_domain = None
        self.visited_links = set()
        self.links_queue = deque()

    def start_requests(self):
        for url in self.start_urls:
            yield scrapy.Request(url, self.parse_domain, dont_filter=True)

    def parse_domain(self, response):
        self.current_domain = urlparse(response.url).netloc
        self.visited_links.clear()
        self.links_queue.clear()
        
        allowed_domain = urlparse(response.url).netloc
        rules = (
            Rule(
                LinkExtractor(
                    allow_domains=[allowed_domain],
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
                        r'.*[\?&]size.*'
                    ]
                ), 
                callback='parse_item', 
                follow=True
            ),
        )
        self._rules = rules
        self._compile_rules()
        
        return self.parse_item(response)

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
            if urlparse(absolute_link).netloc == self.current_domain:
                yield scrapy.Request(absolute_link, callback=self.parse_item)

    def write_links_to_file(self):
        filename = f'{self.current_domain}_links.txt'
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