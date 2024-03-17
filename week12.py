import requests as req
import os
from lxml import etree
import csv
import time
from io import BytesIO
from PIL import Image

from threading import Thread, currentThread, Semaphore
from queue import Queue
from bs4 import BeautifulSoup


def producer(q, s, page):
    """
    获取一个分类下的所有歌单id
    q - 队列
    s - 信号量
    page - 当前页数
    """
    s.acquire()
    print(f'{page}--produce线程开始工作')

    url = 'https://music.163.com//discover/playlist/?order=hot&cat=%E8%AF%B4%E5%94%B1&limit=35&offset='
    url_page = str(35 * (page-1))  # 定位页数
    url = url + url_page
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)'
                      ' Chrome/65.0.3325.181 Safari/537.36'
    }
    response = req.get(url=url, headers=headers)
    html = response.text
    soup = BeautifulSoup(html, 'html.parser')
    ids = soup.select('.dec a')

    print(f'{page}--produce线程结束工作')
    for i in ids:
        q.put(i)
    s.release()


def consumer(q, s, page):
    """
    对每个id，获取歌单的详细信息(一个consumer处理一页歌单, 共35个)
    包括：歌单的封面图片（需把图片保存到本地）、歌单标题、创建者id、创建者昵称、介绍、歌曲数量、播放量、添加到播放列表次数、分享次数、评论数
    """
    s.acquire()
    print(f'{page}--consumer线程开始工作')
    os.mkdir('D:\Myproject\week12\\' + str(page))

    row = ['id', 'title', 'nickname', 'img', 'description', 'count',
           'number of song', 'number of adding list', 'share', 'comment']

    with open(f'D:\Myproject\week12\\playlist{page}.csv', 'w', encoding='utf-8') as f:
        csv_writer = csv.writer(f)
        csv_writer.writerow(row)
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)'
                          ' Chrome/65.0.3325.181 Safari/537.36'
        }

        for i in range(35):
            item = q.get()
            if item is None:
                print('队列为空, consumer进程结束')
                s.release()
                return
            url = 'https://music.163.com/' + item['href']  # 生产者传递的id链接

            response = req.get(url=url, headers=headers)
            html = response.text
            soup = BeautifulSoup(html, 'html.parser')
            id = soup.select('.s-fc7')[0]['href'].split('=')[-1]

            img = soup.select('img')[0]['data-src']  # 图片链接
            res = req.get(img)
            image = Image.open(BytesIO(res.content))  # 图片处理
            try:
                image.save(f'D:\Myproject\week12\\{page}\\{i}.jpg')
            except:
                image.save(f'D:\Myproject\week12\\{page}\\{i}.png')

            title = soup.select('title')[0].get_text()  # 标题
            nickname = soup.select('.s-fc7')[0].get_text()  # 昵称

            description = soup.select('p')[1].get_text()  # 简介
            count = soup.select('strong')[0].get_text()  # 播放次数
            song_number = soup.select('span span')[0].get_text()  # 歌的数目
            add_lis = soup.select('a i')[1].get_text()  # 添加进列表次数
            add_lis = add_lis.replace('(', '')
            add_lis = add_lis.replace(')', '')
            share = soup.select('a i')[2].get_text()  # 分享次数
            share = share.replace('(', '')
            share = share.replace(')', '')
            comment = soup.select('a i')[4].get_text()  # 评论次数
            comment = comment.replace('(', '')
            comment = comment.replace(')', '')

            """
            for link in soup.find_all('meta'):
                # 封面图片
                if link.get('property') == 'og:image':
                    img = req.get(link.get('content'))
                    with open(f'D:\Myproject\week12\\{page}\\{i}.png', 'wb') as f:
                        f.write(img.content)
                # 歌单标题
                elif link.get('property') == 'og:title':
                    title = link.get('content')
                # 歌单介绍
                elif link.get('property') == 'og:description':
                    description = link.get('content')

            for link in soup.find_all('a'):
                if link.get('data-res-id') == str(id):
                    if link.get('data-res-author') is not None and link.get('data-count') is not None:
                        # 创作者昵称, 分享次数
                        nickname = link.get('data-res-author')
                        share = link.get('data-count')
                    # 添加到列表次数
                    elif link.get('data-count') is not None:
                        add_lis = link.get('data-count')

            for link in soup.find_all('span'):
                # 歌曲数量
                if link.get('id') == 'playlist-track-count':
                    song_number = link.string
                # 评论数量
                elif link.get('id') == 'cnt-comment-count':
                    comment = link.string

            for link in soup.find_all('strong'):
                # 播放次数
                count = link.string
            """
            # print([id, title, nickname, img, description, count, song_number, add_lis, share, comment])
            csv_writer.writerow([id, title, nickname, img, description, count, song_number, add_lis, share, comment])

        print(f'{page}--consumer线程结束工作')
        s.release()


def main():

    p_list = []
    c_list = []

    q = Queue()
    pages = 2
    sp = Semaphore(5)
    sc = Semaphore(5)

    for i in range(1, 45):
        p = Thread(target=producer, args=(q, sp, i,))
        p_list.append(p)

    for p in p_list:
        p.start()

    for p in p_list:
        p.join()

    for i in range(1, 45):
        c = Thread(target=consumer, args=(q, sc, i,))
        c_list.append(c)

    for c in c_list:
        c.start()

    for c in c_list:
        q.put(None)

    print('全部运行结束')


if __name__ == '__main__':
    main()