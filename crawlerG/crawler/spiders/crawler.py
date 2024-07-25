import scrapy
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
from urllib.parse import urlparse
import os
from collections import deque

class LinkSpider(CrawlSpider):
    name = "link_spider"
    
    # Read URLs from a file in the same directory as the script
    current_directory = os.path.dirname(os.path.abspath(__file__))
    urls_file_path = os.path.join(current_directory, 'urls.txt')
    
    with open(urls_file_path, 'r') as file:
        start_urls = [line.strip() for line in file.readlines()]

    def __init__(self, *args, **kwargs):
        super(LinkSpider, self).__init__(*args, **kwargs)
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
                        r'.*[\?&]size.*'
                    ]  # Add patterns to deny
                ), 
                callback='parse_item', 
                follow=True
            ),
        )
        super(LinkSpider, self)._compile_rules()
        self.visited_links = set()
        self.links_queue = deque()  # Use a deque to batch writes

    def parse_item(self, response):
        page_links = response.css('a::attr(href)').getall()
        
        for link in page_links:
            absolute_link = response.urljoin(link)
            if absolute_link not in self.visited_links:
                self.visited_links.add(absolute_link)
                self.links_queue.append(absolute_link)
                
                # Batch write if queue size exceeds threshold
                if len(self.links_queue) >= 1000:
                    self.write_links_to_file()

    def write_links_to_file(self):
        output_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'output_links.txt')
        with open(output_file_path, 'a') as f:
            while self.links_queue:
                f.write(self.links_queue.popleft() + "\n")

    def closed(self, reason):
        # Write remaining links when spider is closed
        self.write_links_to_file()
