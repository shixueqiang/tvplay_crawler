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
from tvplay_crawler.items import TvplayCrawlerItem, TvplaySourceItem, TvplayExtend, TvplaySource
from selenium import webdriver
from scrapy.xlib.pydispatch import dispatcher
from scrapy import signals
import operator

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
        for i, link in enumerate(links):
            # if i > 0:
            #     break
            next_url = link.css(
                'div.fl-info dl dt h3 a::attr(href)').extract_first()
            # mLogger.debug(self.domain + next_url)
            vScore = link.css('div.fl-img a span em::text').extract_first(
            ) + link.css('div.fl-img a span::text').extract_first()
            mLogger.debug("分数:" + vScore)
            vTvType = link.css(
                'div.fl-info dl dt h3 a strong::text').extract_first()
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
        if self.cur_page < self.total_page:
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
        statusNode = response.css('div.resource-tit h2 label::text').extract_first()
        status = 3
        if statusNode is not None:
            if "连载中" in statusNode:
                status = 1
            elif "完结" in statusNode:
                status = 2
            elif "已上映" in statusNode:
                status = 2
            else:
                status = 3
        video_info = self.videos.get(vTvType + vName)
        if video_info is not None:
            if "剧" in vTvType:
                video_info['category'] = 1
            elif "电影" in vTvType:
                video_info['category'] = 2
            elif "动画" in vTvType:
                video_info['category'] = 3
            elif "综艺" in vTvType:
                video_info['category'] = 4
            else:
                video_info['category'] = 5
            video_extend = TvplayExtend()
            video_extend['status'] = status
            video_info['video_extend'] = video_extend
            # mLogger.debug(video_extend)
            lis = response.css('div.fl-info ul li')
            for li in lis:
                str1 = li.css('span::text').extract_first()
                str2 = li.css('strong::text').extract_first()
                if str1 is not None:
                    if "地区" in str1:
                        video_info['area'] = str2
                    elif "类型" in str1:
                        video_info['video_type'] = str2
                    elif "首播" in str1:
                        first_play = str2
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
            
            video_sources = []
            mLogger.debug("video_name : " + video_info["video_name"] + " video_sources length : " + str(len(video_info.get('video_sources', []))))
            zimuzu_source = TvplaySource()
            zimuzu_source['source_name'] = '人人影视'
            zimuzu_source['video_src'] = response.url
            zimuzu_source['is_member'] = 1
            zimuzu_source['is_danmu'] = 1
            zimuzu_source['is_on_line'] = 1
            baiduyun_source = TvplaySource()
            baiduyun_source['source_name'] = '百度云'
            baiduyun_source['video_src'] = None
            baiduyun_source['is_member'] = 1
            baiduyun_source['is_danmu'] = 1
            baiduyun_source['is_on_line'] = 0
            weiyun_source = TvplaySource()
            weiyun_source['source_name'] = '微云'
            weiyun_source['video_src'] = None
            weiyun_source['is_member'] = 1
            weiyun_source['is_danmu'] = 1
            weiyun_source['is_on_line'] = 0
            fantexi_source = TvplaySource()
            fantexi_source['source_name'] = '范特西视频'
            fantexi_source['video_src'] = None
            fantexi_source['is_member'] = 1
            fantexi_source['is_danmu'] = 1
            fantexi_source['is_on_line'] = 0
            video_sources.append(zimuzu_source)
            video_sources.append(baiduyun_source)
            video_sources.append(weiyun_source)
            video_sources.append(fantexi_source)
            video_info['video_sources'] = video_sources

            next_url = response.css('div.view-res-list div h3 a::attr(href)').extract_first()
            mLogger.debug("next_url:" + next_url)
            if "http://zmz003.com" in next_url:
                yield response.follow(next_url, callback=self.parse_video_source)
            else:
                yield video_info
    
    #解析视频资源
    def parse_video_source(self, response):
        vTvType = response.css('p.film-title span.type::text').extract_first()
        vName = response.css('p.film-title span.name-chs::text').extract_first()
        vName = vName[vName.index('《') + 1:vName.index('》')]
        mLogger.debug('视频资源:' + vTvType + vName)
        video_info = self.videos.get(vTvType + vName)

        zimuzu_source = self.search_from_videosources("人人影视", video_info['video_sources'])
        if zimuzu_source is not None:
            zimuzu_source_items = []
            zimuzu_source['video_source_items'] = zimuzu_source_items
            seasonNodes = response.xpath("//div[@class='tab-content info-content']/div[contains(@id, 'sidetab')]")
            if seasonNodes is not None:
                renew_num = seasonNodes[0].xpath('@id').extract_first()
                renew_num = renew_num[8:len(renew_num)]
                video_info['video_extend']['renew_num'] = renew_num
                for i, seasonNode in enumerate(seasonNodes):
                    nodeId = seasonNode.xpath('@id').extract_first()
                    # mLogger.debug("序号:" + str(i) + " id = " + nodeId)
                    all_tabs = seasonNode.xpath("./div/div[@class='tab-pane']")
                    # mLogger.debug("all_tabs length:" + str(len(all_tabs)))
                    for tab in all_tabs:
                        #人人影视资源 找到含有中字的标签
                        zhongzi = tab.css("div.infobar span.badge::text").extract_first()
                        tab_text = tab.css("div.infobar::text").extract_first()
                        # if zhongzi is not None:
                        #     mLogger.debug("zhongzi:" + zhongzi)
                        # if tab_text is not None:
                        #     mLogger.debug("tab_text:" + tab_text)
                        if zhongzi is not None and "中字" in zhongzi:
                            item_chinese = tab.css('ul.down-list li')
                            if item_chinese is not None:
                                self.parse_source_item(item_chinese, zimuzu_source_items, tab_text)
                        elif tab_text is not None and "在线" in tab_text:
                            #百度云、微云、范特西视频资源
                            item_app = tab.css('ul.down-list li')
                            if item_app is not None:
                                self.parse_other_source_item(item_app, video_info['video_sources'])
        # mLogger.debug(video_info.video_sources)
        # for video_source in video_info.video_sources:
        #     mLogger.debug(video_source.video_source_items)
        yield video_info

    def parse_source_item(self, items, video_source_items, definition):
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
                        itemJishu = itemJishu[1:itemJishu.index("集")]
                    except:
                        pass
                sources = item.css('ul.down-links li')
                for source in sources:
                    wherefrom = source.css('a p.desc::text').extract_first()
                    if operator.eq(wherefrom, "小米路由器远程离线下载"):
                        continue
                    video_source_item = TvplaySourceItem()
                    video_source_item['name'] = itemName
                    video_source_item['source'] = source.css('a::attr(href)').extract_first()
                    video_source_item['season'] = itemSeason
                    video_source_item['jishu'] = int(itemJishu)
                    video_source_item['definition'] = definition
                    video_source_items.append(video_source_item)

    def parse_other_source_item(self, items, video_sources):
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
                        itemJishu = itemJishu[1:itemJishu.index("集")]
                    except:
                        pass
                sources = item.css('ul.down-links li')
                for source in sources:
                    wherefrom = source.css('a p.desc::text').extract_first()
                    if operator.eq(wherefrom, "人人下载器"):
                        continue
                    video_source = self.search_from_videosources(wherefrom, video_sources)
                    if video_source is not None:
                        video_source_items = video_source.get('video_source_items', [])
                        if len(video_source_items) == 0:
                            video_source['video_source_items'] = video_source_items
                        video_source_item = TvplaySourceItem()
                        video_source_item['name'] = itemName
                        video_source_item['source'] = source.css('a::attr(href)').extract_first()
                        video_source_item['season'] = itemSeason
                        video_source_item['jishu'] = int(itemJishu)
                        video_source_item['definition'] = "在线看"
                        video_source_items.append(video_source_item)

    def search_from_videosources(self, wherefrom, list):
        for video_source in list:
            if operator.eq(wherefrom, video_source['source_name']):
                return video_source
        return None

    
        


