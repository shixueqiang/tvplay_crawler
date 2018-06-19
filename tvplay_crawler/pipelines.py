# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://doc.scrapy.org/en/latest/topics/item-pipeline.html
import logging
from tvplay_crawler import logger
mLogger = logger.Logger(logging.DEBUG)
from tvplay_crawler import filelogger
mFileLogger = filelogger.Logger("zimuzu_spider.log", logging.ERROR)
import pymysql
import datetime
import traceback


class TvplayCrawlerPipeline(object):
    def __init__(self):
        # Connect to the database
        self.connection = pymysql.connect(
            host='192.168.60.217',
            user='shixq',
            password='shixq123',
            db='zhuiju',
            charset='utf8',
            cursorclass=pymysql.cursors.DictCursor)

    def process_item(self, item, spider):
        try:
            if self.get_videoinfo(item['video_name']) != 0:
                pass
            else:
                #插入video_info
                video_id = self.insert_videoinfo(item)
                if self.get_videoextend(video_id) != 0:
                    pass
                else:
                    #插入video_extend
                    video_extend = item['video_extend']
                    video_extend['v_id'] = video_id
                    self.insert_videoextend(video_extend)
                if self.get_videosource(video_id) != 0:
                    pass
                else:
                    #插入video_source
                    video_sources = item['video_sources']
                    mLogger.debug("video_sources length is " +
                                  str(len(video_sources)))
                    for video_source in video_sources:
                        video_source['v_id'] = video_id
                        vs_id = self.insert_videosource(video_source)
                        #先删除vs_id对应的分集资源
                        self.delete_sourceitem(vs_id)
                        #插入video_source_item
                        for video_source_item in video_source.get(
                                'video_source_items', []):
                            video_source_item['v_id'] = video_id
                            video_source_item['vs_id'] = vs_id
                            self.insert_videosource_item(video_source_item)

            # connection is not autocommit by default. So you must commit to save
            # your changes.
            self.connection.commit()
        except Exception:
            mFileLogger.error("数据库操作错误回滚提交\n" + traceback.format_exc())
            self.connection.rollback()
        return item

    def close_spider(self, spider):
        mLogger.debug("关闭mysql数据库连接")
        self.connection.close()

    @classmethod
    def from_crawler(cls, crawler):
        return cls()

    def get_videoinfo(self, video_name):
        video_id = 0
        try:
            with self.connection.cursor() as cursor:
                sql = "SELECT id FROM video_info WHERE video_name = %s"
                cursor.execute(sql, (video_name))
                result = cursor.fetchone()
                if result is not None:
                    video_id = result['id']
        except Exception as e:
            raise Exception(e)
        return video_id

    def get_videosource(self, v_id):
        id = 0
        try:
            with self.connection.cursor() as cursor:
                sql = "SELECT id FROM video_source WHERE v_id = %s"
                cursor.execute(sql, (v_id))
                result = cursor.fetchone()
                if result is not None:
                    id = result['id']
        except Exception as e:
            raise Exception(e)
        return id

    def get_videoextend(self, v_id):
        id = 0
        try:
            with self.connection.cursor() as cursor:
                sql = "SELECT id FROM video_extend WHERE v_id = %s"
                cursor.execute(sql, (v_id))
                result = cursor.fetchone()
                if result is not None:
                    id = result['id']
        except Exception as e:
            raise Exception(e)
        return id

    def insert_videoinfo(self, video_info):
        try:
            with self.connection.cursor() as cursor:
                now = datetime.datetime.now()
                now = now.strftime("%Y-%m-%d %H:%M:%S")
                sql = """INSERT INTO video_info 
                        (video_name, aliases, score, image, category, type, area, video_time, synopsis, years, renew, create_time) 
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""
                cursor.execute(sql, (video_info.get('video_name', None),
                                     video_info.get('aliases', None),
                                     video_info.get('score', None),
                                     video_info.get('image', None),
                                     video_info.get('category', 1),
                                     video_info.get('video_type', None),
                                     video_info.get('area', None),
                                     video_info.get('video_time', None),
                                     video_info.get('synopsis', None),
                                     video_info.get('years', None),
                                     video_info.get('renew', None), now))
        except Exception as e:
            raise Exception(e)
        return int(cursor.lastrowid)

    def insert_videoextend(self, video_extend):
        try:
            with self.connection.cursor() as cursor:
                now = datetime.datetime.now()
                now = now.strftime("%Y-%m-%d %H:%M:%S")
                sql = "INSERT INTO video_extend (v_id, status, renew_num, create_time) VALUES (%s, %s, %s, %s)"
                cursor.execute(sql, (video_extend.get('v_id'),
                                     video_extend.get('status', None),
                                     video_extend.get('renew_num', None), now))
        except Exception as e:
            raise Exception(e)

    def insert_videosource(self, video_source):
        try:
            with self.connection.cursor() as cursor:
                now = datetime.datetime.now()
                now = now.strftime("%Y-%m-%d %H:%M:%S")
                sql = "INSERT INTO video_source (v_id, source_name, video_src, is_member, is_danmu, is_on_line, create_time) VALUES (%s, %s, %s, %s, %s, %s, %s)"
                cursor.execute(sql, (video_source.get('v_id'),
                                     video_source.get('source_name', None),
                                     video_source.get('video_src', None),
                                     video_source.get('is_member', 1),
                                     video_source.get('is_danmu', 1),
                                     video_source.get('is_on_line', 1), now))
        except Exception as e:
            raise Exception(e)
        return int(cursor.lastrowid)

    def insert_videosource_item(self, video_source_item):
        try:
            with self.connection.cursor() as cursor:
                now = datetime.datetime.now()
                now = now.strftime("%Y-%m-%d %H:%M:%S")
                sql = "INSERT INTO video_source_item (v_id, vs_id, name, source, season, jishu, clarity, create_time) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
                cursor.execute(
                    sql, (video_source_item.get('v_id'),
                          video_source_item.get('vs_id'),
                          video_source_item.get('name', None),
                          video_source_item.get('source', None),
                          video_source_item.get('season', None),
                          video_source_item.get('jishu', None),
                          video_source_item.get('definition', None), now))
        except Exception as e:
            raise Exception(e)

    def delete_sourceitem(self, vs_id):
        try:
            with self.connection.cursor() as cursor:
                sql = "DELETE FROM video_source_item WHERE vs_id = %s"
                cursor.execute(sql, (vs_id))
        except Exception as e:
            raise Exception(e)
