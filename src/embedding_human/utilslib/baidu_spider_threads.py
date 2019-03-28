#!/usr/bin/env python
# -*- coding:utf-8 -*-

import os
import sys
import re
import urllib
import json
import socket
import time
import multiprocessing
from multiprocessing.dummy import Pool
from multiprocessing import Queue

import requests

timeout = 5
socket.setdefaulttimeout(timeout)


class Image(object):
    """图片类，保存图片信息"""

    def __init__(self, url, save_path, referer):
        super(Image, self).__init__()
        self.url = url
        self.save_path = save_path
        self.referer = referer


class Crawler:
    # 睡眠时长
    __time_sleep = 0.1
    __amount = 0
    __start_amount = 0
    __counter = 0
    headers = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Ubuntu '
                             'Chromium/58.0.3029.110 Chrome/58.0.3029.110 Safari/537.36'}

    # 获取图片url内容等
    # t 下载图片时间间隔
    def __init__(self, t=0.1):
        self.dirpath = dirpath
        self.time_sleep = t
        self.pool = Pool(30)
        self.session = requests.Session()
        self.session.headers = Crawler.headers
        self.queue = Queue()
        self.delay = 1.5  # 网络请求太频繁会被封
        self.__down_counter = 1

    # 获取后缀名
    @staticmethod
    def __get_suffix(name):
        m = re.search(r'\.[^\.]*$', name)
        if m.group(0) and len(m.group(0)) <= 5:
            return m.group(0)
        else:
            return '.jpeg'

    # 获取前缀
    @staticmethod
    def __get_prefix(name):
        return name[:name.find('.')]

    # 保存图片
    def __resolve_img_url(self, rsp_data, referer):
        imgs = []
        for image_info in rsp_data['imgs']:
            fix = self.__get_suffix(image_info['objURL'])
            local_path = os.path.join(self.__work_path, str(self.__counter) + str(fix))
            image = Image(image_info['objURL'], local_path, referer)
            imgs.append(image)
            print("图片+1,已有" + str(self.__down_counter) + "张")
            self.__down_counter += 1
            self.__counter += 1
        self.queue.put(imgs)
        return

    # 开始获取
    def __resolve_json(self, word=''):
        search = urllib.quote(word)
        # pn 图片数
        pn = self.__start_amount
        while pn < self.__amount:

            url = 'http://image.baidu.com/search/avatarjson?tn=resultjsonavatarnew&ie=utf-8&word=' + search + '&cg=girl&pn=' + str(
                pn) + '&rn=60&itg=0&z=0&fr=&width=&height=&lm=-1&ic=0&s=0&st=-1&gsm=1e0000001e'
            # 沿用session防ban
            try:
                time.sleep(self.delay)
                req = self.session.get(url=url, timeout=15)
                rsp = req.text
            except UnicodeDecodeError as e:
                print(e)
                print('-----UnicodeDecodeErrorurl:', url)
            except requests.exceptions.RequestException as e:
                print(e)
                print("-----Error:", url)
            except socket.timeout as e:
                print(e)
                print("-----socket timout:", url)
            else:
                # 解析json
                try:
                    rsp_data = json.loads(rsp)
                    self.__resolve_img_url(rsp_data, url)
                except ValueError:
                    pass
                # 读取下一页
                print("读取下一页json")
                pn += 60
        print("解析json完成")
        return

    def __downImg(self, img):
        """下载单张图片，传入的是Image对象"""
        # try:
        #     time.sleep(self.delay)
        #     urllib.urlretrieve(img.url, img.save_path)
        # except requests.exceptions.HTTPError as e:
        #     print(e)
        # except Exception as err:
        #     time.sleep(1)
        #     print(err)
        #     print("产生未知错误，放弃保存")

        imgUrl = img.url
        # self.messageQueue.put("线程 %s 正在下载 %s " %
        #          (threading.current_thread().name, imgUrl))
        try:
            time.sleep(self.delay)
            headers = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Ubuntu '
                                     'Chromium/58.0.3029.110 Chrome/58.0.3029.110 Safari/537.36'}
            headers['Referer'] = img.referer
            res = requests.get(imgUrl, headers=headers, timeout=15)
            with open(img.save_path, "wb") as f:
                f.write(res.content)
        except Exception as e:
            message = "抛出异常： %s%s" % (imgUrl, str(e))
            print(message)

    def start(self, index, word, spider_page_num=1, start_page=1):
        """
        爬虫入口
        :param word: 抓取的关键词
        :param spider_page_num: 需要抓取数据页数 总抓取图片数量为 页数x60
        :param start_page: 起始页数
        :return:
        """
        self.__work_path = os.path.join(self.dirpath, index)
        if not os.path.exists(self.__work_path):
            os.mkdir(self.__work_path)
        self.__counter = len(os.listdir(self.__work_path)) + 1  # 判断本地名字是否重复，获取目录下图片数
        self.__start_amount = (start_page - 1) * 60
        self.__amount = spider_page_num * 60 + self.__start_amount

        self.__resolve_json(word)

        while self.queue.qsize():
            imgs = self.queue.get()
            self.pool.map_async(self.__downImg, imgs)
        self.pool.close()
        self.pool.join()
        print('完成保存')


if __name__ == '__main__':
    dirpath = os.path.join(sys.path[0], 'results')
    if not os.path.exists(dirpath):
        os.mkdir(dirpath)

    with open('name.json') as f:
        json_data = json.load(f)
    # word = str(input("请输入图片关键字: \n"))
    sort_data = sorted([(int(k), v) for k, v in json_data.items()])
    print('开始')
    for index, name in sort_data:
        folder = str(index)
        person = name.encode('utf-8')
        print('开始抓取 {}:{}'.format(folder, person))
        if folder in os.listdir('./results'):
            print('已存在, continue')
            continue
        crawler = Crawler(0.05)
        crawler.dirpath = dirpath
        crawler.start(folder, person, 2, 1)
