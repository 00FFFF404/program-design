import jieba
import re
import matplotlib.pyplot as plt
from pyecharts.charts import Geo
from pyecharts import options as opts
from pyecharts.render import make_snapshot
import snapshot

import pprint

file_path = "weibo.txt"
file_name = "Anger makes fake news viral online-data&code/data/emotion_lexicon//"


# 停用词
def stopword_list(filepath):
    stopwords = [line.strip() for line in open(filepath, 'r', encoding='utf-8-sig').readlines()]
    stopwords.append(' ')
    return stopwords


# 将情绪词典加入jieba的自定义词典
def add(filename):
    file = ['anger.txt', 'disgust.txt', 'fear.txt', 'joy.txt', 'sadness.txt']
    for i in range(len(file)):
        jieba.load_userdict(filename + file[i])


# 对微博数据进行清理
def clean(filepath, n):
    """
    清理微博数据，去除
    1.@和回复中的用户名；
    2.去除表情符号、话题、表情和网址；
    3.去除无意义的词汇（“我在：”，“我在这里：”）
    4.去除用户id和+0800（默认中国时间）

    :param filepath: 原始微博数据
    :param n: 处理数据行数

    """
    with open(filepath, encoding="utf-8") as f:
        i = 0
        txt = f.readlines()
        for text in txt:
            if i <= n:
                text = re.sub(r"(回复)?(//)?\s*@\S*?\s*(:| |$)", " ", text)  # 去除正文中的@和回复/转发中的用户名
                text = re.sub(r"\[\S+?\]", "", text)  # 去除表情符号
                text = re.sub(r"#\S+#", "", text)  # 话题内容
                url = re.compile(
                    r'(?i)\b((?:https?://|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|('
                    r'\([^\s( '
                    r')<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:\'".,<>?«»“”‘’]))',
                    re.IGNORECASE)
                text = re.sub(url, "", text)  # 去除网址
                text = re.sub(r"\d{10}[.][0]", "", text)  # 去除用户id
                text = text.replace("我在:", "", )  # 去除无意义的词语
                text = text.replace("我在这里:", "")
                text = text.replace("+0800", "")  # 去除+0800
                text = re.sub(r"\s+", " ", text)  # 合并正文中过多的空格
                i += 1

                file = open('clean_text.txt', 'a', encoding='utf-8')
                file.write(text + '\n')


def cut_pos(file):
    """
    将清理后文本每条微博的地点提取出来
    :param file:已清理的微博数据
    :return:位置列表
    """
    pattern1 = re.compile(r'\[\d{0,3}[.]\d*, \d{0,3}[.]\d*]')
    pattern = re.compile(r'(\d{0,3}[.]\d+)')
    with open(file, encoding='utf-8') as f:
        txt = str(f.readlines())
        result = str(pattern1.findall(txt))
        result = pattern.findall(result)

    for i, v in enumerate(result):
        result[i] = float(v)

    return result


def cut_time(file):
    """
    将清理后文本每条微博的时间提取出来
    :param file: 已清理的微博数据
    :return: 时间列表
    """
    pattern = re.compile(r'\d{2}[:]\d{2}[:]\d{2}')
    with open(file, encoding='utf-8') as f:
        txt = str(f.readlines())
        result = pattern.findall(txt)

    return result


def cut_day(file):
    """
    将清理后文本每条微博的日期提取出来
    :param file: 已清理的微博数据
    :return: 日期列表
    """
    pattern = re.compile(r'\w{3}[ ]\w{3}[ ]\d{2}')
    with open(file, encoding='utf-8') as f:
        txt = str(f.readlines())
        result = pattern.findall(txt)

    return result


def cut_txt(file):
    """
    将清理后文本每条微博的内容提取出来
    :param file: 已清理的微博数据
    :return: 文本列表
    """
    result = []
    with open(file, encoding='utf-8') as f:
        txt = f.readlines()
        i = 0
        for text in txt:
            '''
            text = re.sub(r"\[\d{0,3}[.]\d*, \d{0,3}[.]\d*]", "", text)
            text = re.sub(r"\d{2}[:]\d{2}[:]\d{2}", "", text)
            text = re.sub(r"\w{3}[ ]\w{3}[ ]\d{2}", "", text)
            text = text.replace("2013 \n", "")
            text = re.sub(r"\s+", " ", text)
            '''
            text = re.sub(r"[^\u4e00-\u9fa5]+", "", text)  # 只保留中文
            if i >= 1:
                result.append(text)
            i += 1

    return result


def text_cut(file):
    """
    综合地点、时间、日期、文本提取函数，并对文本进行分词，构建每一条微博为一个字典的字典列表
    :param file: 已清理的微博数据
    :return: list（字典列表）
    """
    lst = []
    pos = cut_pos(file)
    lat = []  # 纬度
    lon = []  # 经度
    for i in range(len(pos)):
        if i % 2 == 0:
            lat.append(pos[i])
        else:
            lon.append(pos[i])

    time = cut_time(file)
    day = cut_day(file)
    txt = cut_txt(file)

    for i in range(len(lat)):
        dic = dict(zip(['lat', 'lon', 'time', 'day', 'txt'], [lat[i], lon[i], time[i], day[i], txt[i]]))
        lst.append(dic)

    '''
    进行每条微博的分词：
    1.导入情绪词典
    2.导入停用词
    '''
    add(file_name)

    for i in range(len(lst)):
        result = []  # 分词列表
        cut_l = jieba.lcut(lst[i].get('txt'))
        for j in cut_l:
            if j not in stopword_list("stopwords_list.txt"):
                result.append(j)
        lst[i]['txt'] = result

    return lst

    # pprint.pprint(lst)


def count_emotion(txt):
    """
    计算每种情绪出现多少次
    :param txt:已分词的一条微博，列表形式
    :return:
    """
    anger = []
    disgust = []
    fear = []
    joy = []
    sadness = []
    with open(file_name + 'anger.txt', 'r', encoding='utf-8') as f1:
        for line in f1.readlines():
            line = line.strip('\n')
            anger.append(line)
    with open(file_name + 'disgust.txt', 'r', encoding='utf-8') as f2:
        for line in f2.readlines():
            line = line.strip('\n')
            disgust.append(line)
    with open(file_name + 'fear.txt', 'r', encoding='utf-8') as f3:
        for line in f3.readlines():
            line = line.strip('\n')
            fear.append(line)
    with open(file_name + 'joy.txt', 'r', encoding='utf-8') as f4:
        for line in f4.readlines():
            line = line.strip('\n')
            joy.append(line)
    with open(file_name + 'sadness.txt', 'r', encoding='utf-8') as f5:
        for line in f5.readlines():
            line = line.strip('\n')
            sadness.append(line)

    def count_emo(kind):
        """
        判断微博某情绪出现次数
        :param kind: 情绪类型（anger/disgust/.../sadness）
        :return: 该情绪出现次数
        """
        nonlocal txt, anger, disgust, fear, joy, sadness
        num = 0  # 某情绪出现次数
        if kind == 'anger':
            for i in range(len(txt)):
                if (txt[i]) in anger:
                    num += 1
        if kind == 'disgust':
            for i in range(len(txt)):
                if (txt[i]) in disgust:
                    num += 1
        if kind == 'fear':
            for i in range(len(txt)):
                if (txt[i]) in fear:
                    num += 1
        if kind == 'joy':
            for i in range(len(txt)):
                if (txt[i]) in joy:
                    num += 1
        if kind == 'sadness':
            for i in range(len(txt)):
                if (txt[i]) in sadness:
                    num += 1

        return num

    return count_emo


def emo_vector(ob):
    """
    生成每条微博的情绪向量 & 情绪，并添加进字典列表中
    :param ob: 字典列表
    :return: 字典列表
    """
    emo_kind = ['anger', 'disgust', 'fear', 'joy', 'sadness']

    for i in range(len(ob)):
        """
        txt - 已经过分词处理的一条微博文本部分
        vector - 该条微博的情绪向量
        """
        txt = ob[i]['txt']
        vector = [0, 0, 0, 0, 0]  # ['anger', 'disgust', 'fear', 'joy', 'sadness']
        emo_count = [0, 0, 0, 0, 0]
        fun = count_emotion(txt)

        # 更新每一情绪计数
        for j in range(5):
            emo_count[j] = fun(emo_kind[j])

        # 生成情绪向量
        maxi = max(emo_count)
        if maxi != 0:
            # 非[0, 0, 0, 0, 0]情况
            if emo_count.count(maxi) > 1:
                for k in range(5):
                    if emo_count[k] == maxi:
                        vector[k] = 1
            else:
                vector[emo_count.index(maxi)] = 1
            ob[i].setdefault('emotion_vector', vector)
        else:
            ob[i].setdefault('emotion_vector', vector)
    return ob


def plot_emo(emotion, time, ob):
    """
    绘制某一情绪在不同时间模式（小时/周/月）的曲线
    :param emotion:情绪类型（anger/disgust/.../sadness）
    :param time:时间模式（hour/week/month）
    :param ob:字典列表
    """

    def to_num(emotion):
        dic = {'anger': 0, 'disgust': 1, 'fear': 2, 'joy': 3, 'sadness': 4}
        return dic[emotion]

    hour = ['{:0>2d}'.format(i) for i in range(24)]
    hour_dict = {}
    hour_dict = hour_dict.fromkeys(hour, 0)

    week = ['Mon', 'Tus', 'Wed', 'Ths', 'Fri', 'Sat', 'Sun']
    week_dict = {}
    week_dict = week_dict.fromkeys(week, 0)

    month = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    month_dict = {}
    month_dict = month_dict.fromkeys(month, 0)

    if time == 'hour':
        # time 格式 - 22:08:28
        for i in range(len(ob)):
            em = to_num(emotion)
            # 查找该微博的情绪向量所对应的情绪是否出现
            if ob[i]['emotion_vector'][em] == 1:
                tm = ob[i]['time'].split(':')
                hour_dict[tm[0]] += 1
        h_value = []
        for v in hour_dict.values():
            h_value.append(v)
        plt.plot(hour, h_value, '-o', label='hour_{}'.format(emotion))
        plt.xlabel('hour')
        plt.ylabel('times')
        plt.legend(loc='best')
        for a, b in zip(hour, h_value):
            plt.text(a, b + 0.1, b, ha='center', va='bottom', fontsize=10)
        plt.savefig('{}_{}.png'.format(time, emotion), dpi=800)
        plt.show()

    if time == 'week':
        # Fir Oct 11
        for i in range(len(ob)):
            em = to_num(emotion)
            if ob[i]['emotion_vector'][em] == 1:
                tm = ob[i]['day'].split(' ')
                week_dict[tm[0]] += 1
        w_value = []
        for v in week_dict.values():
            w_value.append(v)
        plt.plot(week, w_value, 'o-', label='week_{}'.format(emotion))
        plt.xlabel('week')
        plt.ylabel('times')
        plt.legend(loc='best')  # 图例
        for a, b in zip(week, w_value):
            plt.text(a, b + 0.1, b, ha='center', va='bottom', fontsize=10)
        plt.savefig('{}_{}.png'.format(time, emotion), dpi=800)
        plt.show()

    if time == 'month':
        # Fir Oct 11
        for i in range(len(ob)):
            em = to_num(emotion)
            if ob[i]['emotion_vector'][em] == 1:
                tm = ob[i]['day'].split(' ')
                month_dict[tm[1]] += 1
        m_value = []
        for v in month_dict.values():
            m_value.append(v)
        plt.plot(month, m_value, 'o-', label='month_{}'.format(emotion))
        plt.xlabel('month')
        plt.ylabel('times')
        plt.legend(loc='best')  # 图例
        for a, b in zip(month, m_value):
            plt.text(a, b + 0.1, b, ha='center', va='bottom', fontsize=10)
        plt.savefig('{}_{}.png'.format(time, emotion), dpi=800)
        plt.show()


def find_center(ob):
    lat = 0
    lon = 0
    for i in range(len(ob)):
        lat += ob[i]['lat']
        lon += ob[i]['lon']
    lat = lat / len(ob)
    lon = lon / len(ob)

    return lat, lon


def emo_loc(ob):
    lat, lon = find_center(ob)
    print('中心为：' + str(lat) + ',' + str(lon))

    def emo_num(dis, emo):
        emo_kind = ['anger', 'disgust', 'fear', 'joy', 'sadness']
        k = emo_kind.index(emo)
        ans = 0
        for i in range(len(ob)):
            if (lat - ob[i]['lat']) ** 2 + (lon - ob[i]['lon']) ** 2 <= dis ** 2:
                if ob[i]['emotion_vector'][k] == 1:
                    ans += 1
        print('距离中心' + str(dis) + '距离内，' + emo + '数量为：' + str(ans))

        return ans

    return emo_num


def geo_emo(ob):
    """
    在地图上标注出不同情绪的空间分布
    :param ob: 字典列表
    """
    emo_kind = ['anger', 'disgust', 'fear', 'joy', 'sadness']
    emo = {'anger': 5, 'disgust': 15, 'fear': 25, 'joy': 35, 'sadness': 45}
    g = Geo()
    g.add_schema(maptype='北京')
    for i in range(len(ob)):
        if ob[i]['emotion_vector'] != [0, 0, 0, 0, 0]:
            for j in emo_kind:
                if ob[i]['emotion_vector'][emo_kind.index(j)] == 1:
                    g.add_coordinate(name=j, longitude=ob[i]['lon'], latitude=ob[i]['lat'])
                    g.add(series_name='',
                          data_pair=[(j+str(i), emo[j])],
                          type_='scatter',
                          symbol_size=5)
    g.set_series_opts(label_opts=opts.LabelOpts(is_show=False))
    g.set_global_opts(
        visualmap_opts=opts.VisualMapOpts(
            is_piecewise=True,
            pieces=[
                {'min': 1, 'max': 10, 'label': 'anger', 'color': '#DD0200'},
                {'min': 10, 'max': 20, 'label': 'disgust', 'color': 'FCF84D'},
                {'min': 20, 'max': 30, 'label': 'fear', 'color': '#E2C568'},
                {'min': 30, 'max': 40, 'label': 'joy', 'color': '#81AE9F'},
                {'min': 40, 'max': 50, 'label': 'sadness', 'color': '#3700A4'}
            ]
        ),
        title_opts=opts.TitleOpts(title='情绪分布空间图')
    )

    return g


def main():
    clean(file_path, 1000)
    lst = text_cut("clean_text.txt")
    lst = emo_vector(lst)
    # pprint.pprint(lst[0:10])
    '''
    plot_emo(emotion='anger', time='hour', ob=lst)
    plot_emo(emotion='sadness', time='hour', ob=lst)
    plot_emo(emotion='fear', time='week', ob=lst)

    loca = emo_loc(lst)
    loca(2, 'joy')
    loca(3, 'sadness')
    '''

    g = geo_emo(lst)
    g.render('geo_emo.html')


if __name__ == "__main__":
    main()
