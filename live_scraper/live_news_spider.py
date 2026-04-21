import os
import re
from datetime import datetime, timezone
from urllib.parse import urlparse
from scrapy.spiders import SitemapSpider
from scrapy import signals

class LiveGreekNewsSpider(SitemapSpider):
    name = "live_greek_news"
    
    custom_settings = {
        'CLOSESPIDER_ITEMCOUNT': 8000, 
        'DOWNLOAD_DELAY': 3.0, 
        'CONCURRENT_REQUESTS_PER_DOMAIN': 1, 
        'USER_AGENT': 'Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)',
        'DEFAULT_REQUEST_HEADERS': {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'el-GR,el;q=0.9,en-US;q=0.8,en;q=0.7',
        },
        'AUTOTHROTTLE_ENABLED': True,
        'AUTOTHROTTLE_TARGET_CONCURRENCY': 1.0,
        'FEED_EXPORT_ENCODING': 'utf-8'
    }

    sitemap_urls = [
        'https://www.iefimerida.gr/sitemap.xml',
        'https://www.protothema.gr/sitemap/newsarticles/sitemap_index.xml'
    ]
    
    sitemap_rules = [
        (r'/politics/|/economy/|/world/|/greece/', 'parse'),
        (r'/politiki/|/oikonomia/|/kosmos/|/ellada/', 'parse')
    ]

    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super(LiveGreekNewsSpider, cls).from_crawler(crawler, *args, **kwargs)
        crawler.signals.connect(spider.spider_closed, signal=signals.spider_closed)
        return spider

    def __init__(self, *args, **kwargs):
        super(LiveGreekNewsSpider, self).__init__(*args, **kwargs)
        self.state_file = 'last_scraped_time.txt'
        self.newest_timestamp = None
        
        if os.path.exists(self.state_file):
            with open(self.state_file, 'r') as f:
                saved_time = f.read().strip()
                self.cutoff_date = datetime.fromisoformat(saved_time)
        else:
            self.cutoff_date = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)

    def sitemap_filter(self, entries):
        sitemap_page_count = 0
        
        for entry in entries:
            loc = entry.get('loc', '')
            
            if 'sitemap' in loc.lower():
                sitemap_page_count += 1
                if sitemap_page_count > 2:
                    continue
            
            lastmod = entry.get('lastmod')
            if lastmod and self.cutoff_date:
                try:
                    clean_str = lastmod.replace('Z', '+00:00')
                    entry_date = datetime.fromisoformat(clean_str)
                    if not entry_date.tzinfo:
                        entry_date = entry_date.replace(tzinfo=timezone.utc)
                    
                    if entry_date >= self.cutoff_date:
                        yield entry
                except ValueError:
                    yield entry
            else:
                yield entry

    def spider_closed(self, spider):
        if self.newest_timestamp:
            with open(self.state_file, 'w') as f:
                f.write(self.newest_timestamp.isoformat())

    def parse(self, response):
        domain = urlparse(response.url).netloc
        article_data = None

        if 'protothema.gr' in domain:
            article_data = self.extract_protothema(response)
        elif 'iefimerida.gr' in domain:
            article_data = self.extract_iefimerida(response)

        if article_data and article_data.get('date'):
            article_date_obj = self.parse_datetime(article_data['date'])
            
            if article_date_obj:
                if not article_date_obj.tzinfo:
                    article_date_obj = article_date_obj.replace(tzinfo=timezone.utc)

                if article_date_obj > self.cutoff_date:
                    if not self.newest_timestamp or article_date_obj > self.newest_timestamp:
                        self.newest_timestamp = article_date_obj
                    yield article_data

    def extract_protothema(self, response):
        return {
            'source': 'protothema.gr',
            'url': response.url,
            'title': self.clean_text(response.css('h1::text').get()),
            'date': response.css('time::attr(datetime)').get(default='').strip(),
            'text': self.clean_text(' '.join(response.css('.cnt *::text').getall()))
        }

    def extract_iefimerida(self, response):
        return {
            'source': 'iefimerida.gr',
            'url': response.url,
            'title': self.clean_text(response.css('h1::text').get()),
            'date': response.css('.created::text, time::attr(datetime)').get(default='').strip(),
            'text': self.clean_text(' '.join(response.css('.field--name-body p::text, .article-main-body p::text').getall()))
        }

    def parse_datetime(self, date_string):
        try:
            clean_str = date_string.replace('Z', '+00:00')
            return datetime.fromisoformat(clean_str)
        except ValueError:
            match = re.search(r'\b(20\d{2})-(\d{2})-(\d{2})\b', date_string)
            if match:
                return datetime(int(match.group(1)), int(match.group(2)), int(match.group(3)), tzinfo=timezone.utc)
            return None

    def clean_text(self, text):
        if text:
            return ' '.join(text.split())
        return None