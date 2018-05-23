# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/items.html

import scrapy


class TvplaySourceItem(scrapy.Item):
    id = scrapy.Field()
    v_id = scrapy.Field()
    vs_id = scrapy.Field()
    name = scrapy.Field()
    source = scrapy.Field()
    #第几季
    season = scrapy.Field()
    #第几集
    jishu = scrapy.Field()
    definition = scrapy.Field()


class TvplaySource(scrapy.Item):
    id = scrapy.Field()
    v_id = scrapy.Field()
    source_name = scrapy.Field()
    video_src = scrapy.Field()
    is_member = scrapy.Field()
    is_danmu = scrapy.Field()
    is_on_line = scrapy.Field()
    video_source_items = []


class TvplayCrawlerItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    id = scrapy.Field()
    video_name = scrapy.Field()
    #别名
    aliases = scrapy.Field()
    score = scrapy.Field()
    image = scrapy.Field()
    category = scrapy.Field()
    area = scrapy.Field()
    #上映日期
    video_time = scrapy.Field()
    #年份
    years = scrapy.Field()
    #简介
    synopsis = scrapy.Field()
    #周播剧 周几播
    renew = scrapy.Field()
    #英剧/美剧
    tv_type = scrapy.Field()
    video_source = TvplaySource(v_id=id)
