from spiders import zimuzu_spider
from scrapy.crawler import CrawlerProcess
from scrapy.settings import Settings
import settings as my_settings

if __name__ == '__main__':
    zimuzuSpider = zimuzu_spider.ZimuzuSpider()
    crawler_settings = Settings()
    crawler_settings.setmodule(my_settings)
    process = CrawlerProcess(settings=crawler_settings)
    process.crawl(zimuzuSpider)
    process.start(
    )  # the script will block here until the crawling is finished
