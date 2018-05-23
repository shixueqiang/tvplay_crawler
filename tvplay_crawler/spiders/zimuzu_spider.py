import scrapy
import logging
from urllib.parse import urlparse, parse_qs
from scrapy.crawler import CrawlerProcess
import sys
sys.path.append("..")
from tvplay_crawler import logger
mLogger = logger.Logger(logging.DEBUG)
from tvplay_crawler import filelogger
mFileLogger = filelogger.Logger("zimuzu_spider.log", logging.ERROR)
from tvplay_crawler.items import TvplayCrawlerItem, TvplaySourceItem
from selenium import webdriver
from scrapy.xlib.pydispatch import dispatcher
from scrapy import signals

class ZimuzuSpider(scrapy.Spider):
    domain = 'http://www.zimuzu.tv'
    name = "zimuzu"
    allowed_domains = ["zimuzu.tv", "zmz003.com"]
    start_urls = [
        "http://www.zimuzu.tv/resourcelist?channel=&area=&category=&year=&tvstation=&sort=rank&page=1"
    ]
    #每页个数
    page_count = 20
    #当前页
    cur_page = 1
    #总页数
    total_page = 638
    #字典
    videos = {}

    def __init__(self):
        fireFoxOptions = webdriver.FirefoxOptions()
        fireFoxOptions.set_headless()
        self.browser = webdriver.Firefox(firefox_options=fireFoxOptions)
        #spider关闭信号和spider_spider_closed函数绑定
        dispatcher.connect(self.spider_closed, signals.spider_closed)

    def spider_closed(self, spider):
        self.browser.quit()

    #解析视频列表页
    def parse(self, response):
        self.cur_page = int(
            response.css('div.pages div b a.cur::text').extract()[0])
        mLogger.debug('当前页:' + str(self.cur_page))
        links = response.css('div.resource-showlist ul li.clearfix')
        self.page_count = len(links)
        mLogger.debug('当前页个数:' + str(self.page_count))
        for link in links:
            next_url = link.css(
                'div.fl-info dl dt h3 a::attr(href)').extract_first()
            mLogger.debug(self.domain + next_url)
            vScore = link.css('div.fl-img a span em::text').extract_first(
            ) + link.css('div.fl-img a span::text').extract_first()
            mLogger.debug("分数:" + vScore)
            vTvType = link.css(
                'div.fl-info dl dt h3 a strong::text').extract_first()
            mLogger.debug("类型:" + vTvType)
            title = link.css('div.fl-info dl dt h3 a::text').extract_first()
            vName = title[title.index('《') + 1:title.index('》')]
            mLogger.debug("名称:" + vName)
            video_info = TvplayCrawlerItem()
            video_info['score'] = vScore
            video_info['video_name'] = vName
            video_info['tv_type'] = vTvType
            self.videos[vTvType + vName] = video_info
            yield response.follow(
                self.domain + next_url, callback=self.parse_info)
        pages = response.css('div.pages div a::attr(href)').extract()
        if pages is not None and len(pages) > 0:
            last_page = self.domain + pages[len(pages) - 1]
            parsed_url = urlparse(last_page)
            self.total_page = int(parse_qs(parsed_url.query)['page'][0])
        mLogger.debug('总页数:' + str(self.total_page))
        if self.cur_page < 1:
            yield response.follow(
                'http://www.zimuzu.tv/resourcelist?channel=&area=&category=&year=&tvstation=&sort=rank&page='
                + str(self.cur_page + 1),
                callback=self.parse)

    #解析视频详情
    def parse_info(self, response):
        title = response.css('div.resource-tit h2::text').extract_first()
        mLogger.debug("视频详情:" + title)
        vName = title[title.index('《') + 1:title.index('》')]
        mLogger.debug("视频名称:" + vName)
        vTvType = title[title.index('【') + 1:title.index('】')]
        mLogger.debug("剧类型:" + vTvType)
        video_info = self.videos.get(vTvType + vName)
        if video_info is not None:
            lis = response.css('div.fl-info ul li')
            for li in lis:
                str1 = li.css('span::text').extract_first()
                str1 = str1 is None and 'null' or str1
                str2 = li.css('strong::text').extract_first()
                str2 = str2 is None and 'null' or str2
                listr = str1 + str2
                if "地区" in listr:
                    video_info['area'] = listr[listr.index("地区") + 3:len(listr)]
                elif "类型" in listr:
                    video_info['category'] = listr[listr.index("类型") + 3:len(listr)]
                elif "首播" in listr:
                    first_play = listr[listr.index("首播") + 3:len(listr)]
                    if first_play is not None:
                        video_info['video_time'] = first_play.split(' ')[0]
                        video_info['years'] = video_info['video_time'][0:4]
                        try:
                            video_info['renew'] = first_play.split(' ')[1]
                        except:
                            pass
            vAliases = response.css('div.fl-info ul li.mg::text').extract_first()
            video_info['aliases'] = vAliases
            vImage = response.css('div.fl-img div.imglink a img::attr(src)').extract_first()
            video_info['image'] = vImage
            vSynopsisList = response.css('div.resource-desc div.con::text').extract()
            vSynopsis = "".join(vSynopsisList)
            vSynopsis = vSynopsis.replace("【版权方要求，本站仅提供字幕，请站内搜索下载】","")
            video_info['synopsis'] = vSynopsis
            video_source = video_info.video_source
            video_source['source_name'] = '人人影视'
            video_source['video_src'] = response.url
            video_source['is_member'] = 1
            video_source['is_danmu'] = 1
            video_source['is_on_line'] = 1

            next_url = response.css('div.view-res-list div h3 a::attr(href)').extract_first()
            mLogger.debug("next_url:" + next_url)
            yield response.follow(next_url, callback=self.parse_video_source)
    
    #解析视频资源
    def parse_video_source(self, response):
        vTvType = response.css('p.film-title span.type::text').extract_first()
        vTvType = vTvType is None and "null" or vTvType
        vName = response.css('p.film-title span.name-chs::text').extract_first()
        vName = vName is None and "null" or vName[vName.index('《') + 1:vName.index('》')]
        mLogger.debug('视频资源:' + vTvType + vName)
        video_info = self.videos.get(vTvType + vName)
        video_source_items = video_info.video_source.video_source_items
        item_720p = response.css('div#tab-g7-720P ul.down-list li')
        item_1080p = response.css('div#tab-g7-1080P ul.down-list li')
        self.parse_source_item(item_720p, video_source_items)
        self.parse_source_item(item_1080p, video_source_items)
        mLogger.debug(video_info)
        # mLogger.debug(video_info.video_source)
        # mLogger.debug(video_source_items)

    def parse_source_item(self, items, video_source_items):
        if items is not None:
            for item in items:
                itemName = item.css('div.title span.filename::text').extract_first()
                itemSeasonJishu = item.css('div.title span.episode::text').extract_first()
                itemSeason = None
                itemJishu = None
                if itemSeasonJishu is not None:
                    seasonAndJishu = itemSeasonJishu.split(' ')
                    try:
                        itemSeason = seasonAndJishu[0]
                    except:
                        pass
                    try:
                        itemJishu = seasonAndJishu[1]
                    except:
                        pass
                itemDefinition = '720p'
                sources = item.css('ul.down-links li')
                for source in sources:
                    video_source_item = TvplaySourceItem()
                    video_source_item['name'] = itemName
                    video_source_item['source'] = source.css('a::attr(href)').extract_first()
                    video_source_item['season'] = itemSeason
                    video_source_item['jishu'] = itemJishu
                    video_source_item['definition'] = itemDefinition
                    video_source_items.append(video_source_item)

    
        


