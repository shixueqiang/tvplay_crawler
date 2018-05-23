import logging, os


class Logger:
    def __init__(self, path, Flevel=logging.ERROR):
        self.logger = logging.getLogger(path)
        self.logger.setLevel(logging.ERROR)
        fmt = logging.Formatter('[%(asctime)s] [%(levelname)s] %(message)s',
                                '%Y-%m-%d %H:%M:%S')
        #设置文件日志
        fh = logging.FileHandler(path)
        fh.setFormatter(fmt)
        fh.setLevel(Flevel)
        self.logger.addHandler(fh)

    def debug(self, message):
        self.logger.debug(message)

    def info(self, message):
        self.logger.info(message)

    def war(self, message):
        self.logger.warn(message)

    def error(self, message):
        self.logger.error(message)

    def cri(self, message):
        self.logger.critical(message)


if __name__ == '__main__':
    logyyx = Logger('spider.log', logging.ERROR)
    logyyx.debug('一个debug信息')
    logyyx.info('一个info信息')
    logyyx.war('一个warning信息')
    logyyx.error('一个error信息')
    logyyx.cri('一个致命critical信息')
