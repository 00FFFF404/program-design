import time
import csv
import gevent
import requests
import asyncio
import aiofiles
from io import BytesIO
from PIL import Image
import requests as req
from bs4 import BeautifulSoup


def get_id(song_type, page):
    """
    获取指定类型指定页数上全部35个歌单id
    :param song_type: str 歌单类型
    :param page: int 歌单页
    :return: list 返回page页上的35个歌单的id列表
    """
    url = 'https://music.163.com//discover/playlist/?order=hot&cat=' + song_type + '&limit=35&offset='
    url_page = str(35 * (page - 1))  # 定位页数
    url = url + url_page
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)'
                      ' Chrome/65.0.3325.181 Safari/537.36'
    }
    response = req.get(url=url, headers=headers)
    html = response.text
    soup = BeautifulSoup(html, 'html.parser')
    ids = soup.select('.dec a')

    return ids


async def get_top(id):
    """
    获取播放量大于100万的歌单
    :param id: int 歌单id
    :return: int 歌单id
    """
    url = 'https://music.163.com/' + str(id)
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)'
                      ' Chrome/65.0.3325.181 Safari/537.36'
    }
    response = req.get(url=url, headers=headers)
    html = response.text
    soup = BeautifulSoup(html, 'html.parser')
    count = soup.select('strong')[0].get_text()

    if int(count) > 1000000:
        return id
    else:
        return -1


async def get_song(id):
    """获取某歌单前十首歌曲"""
    url = 'https://music.163.com/' + str(id)
    print(url)
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)'
                      ' Chrome/65.0.3325.181 Safari/537.36'
    }
    response = req.get(url=url, headers=headers)
    html = response.text
    soup = BeautifulSoup(html, 'html.parser')
    title = soup.select('title')[0].get_text()  # 标题

    song_dic = {}
    cont = 0
    for link in soup.find_all('a'):
        if '/song?id=' in str(link.get('href')):
            cont += 1
            if cont == 11:
                break  # 不下载客户端只可以看前十首歌
            song_dic.setdefault(f'{link.string}', 'https://music.163.com/' + link['href'])
            # /song?id=1444959590

    print(f'歌单 {title} 前十首歌曲:')
    for song, web in song_dic.items():
        print(f'歌曲名:{song}----->{web}')


async def get_all(id):
    """
    获取歌单全部信息
    歌单的封面图片（需把图片保存到本地）、歌单标题、创建者id、创建者昵称、介绍、歌曲数量、播放量、添加到播放列表次数、分享次数、评论数
    :param id: int 歌单id
    :return: list 包含歌单全部信息
    """
    url = 'https://music.163.com/' + str(id)

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)'
                      ' Chrome/65.0.3325.181 Safari/537.36'
    }
    response = req.get(url=url, headers=headers)
    html = response.text
    soup = BeautifulSoup(html, 'html.parser')
    idd = soup.select('.s-fc7')[0]['href'].split('=')[-1]  # 获取歌单id
    img = soup.select('img')[1].get('src')  # 图片链接
    res = req.get(img)
    image = Image.open(BytesIO(res.content))  # 图片处理
    title = soup.select('title')[0].get_text()  # 标题
    tt = title
    t = ''
    if '|' in tt:
        tt = tt.split('|')
        for _ in tt:
            t += str(_)
    try:
        image.save(f'D:\Myproject\week14\\{t}.jpg')
    except:
        image.save(f'D:\Myproject\week14\\{t}.png')

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

    ls = [idd, title, nickname, img, description, count, song_number, add_lis, share, comment]

    print(ls)


"""def coroutine1():
    # 获取某歌单前十首歌曲信息
    job_list = []
    id_list = get_id('说唱', 1)
    for i in range(len(id_list)):
        id = id_list[i]['href']
        job = gevent.spawn(get_top, id)
        job_list.append(job)
        gevent.joinall(job_list)


def coroutine2():
    # 获取歌单全部信息
    job_list = []
    id_list = get_id('说唱', 1)
    for i in range(len(id_list)):
        id = id_list[i]['href']
        job = gevent.spawn(get_all, id)
        job_list.append(job)
        gevent.joinall(job_list)
"""


def main():
    id_list = get_id('说唱', 4)

    for i in range(len(id_list)):
        id_list[i] = id_list[i]['href']

    print(f'原始歌单列表:{id_list}')
    # 利用协程处理歌单
    loop = asyncio.get_event_loop()
    task1 = []
    final_list = []
    for i in range(len(id_list)):
        task1.append(loop.create_task(get_top(id_list[i])))
    loop.run_until_complete(asyncio.wait(task1))
    for i in range(len(task1)):
        if task1[i].result() != -1:
            final_list.append(task1[i].result())
    print(f'处理后歌单id列表:{final_list}')

    # 获取前十首歌
    task2 = []
    for id in final_list:
        task2.append(loop.create_task(get_song(id)))
    loop.run_until_complete(asyncio.wait(task2))

    # 获取详细信息
    print('歌单详细信息如下:')
    task3 = []
    for id in final_list:
        task3.append(loop.create_task(get_all(id)))
    loop.run_until_complete(asyncio.wait(task3))


if __name__ == '__main__':
    main()
