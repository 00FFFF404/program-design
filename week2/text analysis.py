import jieba
from tqdm.autonotebook import tqdm
import numpy as np
import pandas as pd
import random
import math
import re
from wordcloud import WordCloud
import matplotlib.pyplot as plt

filename = "danmuku.csv"
filepath = "stopwords_list.txt"
jieba.load_userdict("user.txt")


# 随机选取一个弹幕进行分词
def random_segment():
    r_num = random.randint(0, 279900)
    data = pd.read_csv(filename)
    x = data['content'][r_num:r_num + 1]
    print(x[r_num])
    print(jieba.lcut(x[r_num]))


# 停用词
def stopword_list(filepath):
    stopwords = [line.strip() for line in open(filepath, 'r', encoding='utf-8-sig').readlines()]
    stopwords.append(' ')
    return stopwords


# 对原始弹幕库进行预处理，取第一列前n行进行后续分析，length = n
def ppcs(length):
    data = pd.read_csv(filename)
    # data_len = len(data['content'])
    x = data['content'][0:length]
    return x


# 弹幕过滤，过滤”23333“哈哈哈哈”"啊啊““hhh”等无意义弹幕与过短弹幕,输入为预处理后弹幕信息，输出为过滤后弹幕信息
def clean(aft_ppcs):
    new_list = []
    pattern = r"[1-9]|[a-z]|[哈啊]+"
    for i in tqdm(aft_ppcs, desc="弹幕过滤进度", ncols=80):
        if (re.match(pattern, i) is None) and len(i) > 3:
            new_list.append(i)
    return new_list


# 词频统计，输入为预处理后弹幕信息，返回为词频字典
def word_frequency(ob):
    # 建立词频字典
    dic = {}
    # 遍历每一条弹幕并分词
    for i in tqdm(range(len(ob)), desc="词频统计进度", ncols=80):
        result = jieba.lcut(ob[i])
        for j in result:
            # 判断j是否在停用词里
            if j not in stopword_list(filepath):
                if j in dic:
                    dic[j] += 1
                else:
                    dic.setdefault(j, 1)
    return dic


# 去除低频词（出现次数<5），输入为原始词频字典，输出为特征词组成的特征集
def s_feature(dic):
    # 去除词频小于5次的词语
    vocab = {}
    for word in dic:
        if dic[word] > 5:
            vocab.setdefault(word, dic[word])
    return vocab


# 生成one-hot矩阵，输入为预处理后弹幕信息与特征集
def onehot_matrix(ob, dic):
    # 建立一个m行n列的0矩阵，m为弹幕样本数，n为高频词数（词频>5)
    n = len(dic)
    m = len(ob)
    one_hot = np.zeros((m, n))

    for i, comment in enumerate(ob):
        for word in jieba.lcut(comment):
            if word in dic:
                pos = {key: index for index, key in enumerate(dic)}.get(word)
                one_hot[i][pos] = 1
    return one_hot


# 计算两向量余弦相似度
def cosine_simi(x, y):
    s, sumx_2, sumy_2 = 0, 0, 0
    for i in range(len(x)):
        s += x[i] * y[i]
        sumx_2 += pow(x[i], 2)
        sumy_2 += pow(y[i], 2)
    den_x = math.sqrt(sumx_2)
    den_y = math.sqrt(sumy_2)
    if den_x == 0 or den_y == 0:
        return 0.0
    else:
        return s/(den_x * den_y)


# 随机两向量计算余弦相似度，输入为预处理后弹幕信息与onehot矩阵
def random_simi(ob, oht):
    row = len(ob)
    x1, x2 = random.randint(0, row), random.randint(0, row)
    print("选取弹幕1：", ob[x1])
    print("选取弹幕2：", ob[x2])
    return cosine_simi(oht[x1], oht[x2])


# 生成词云，输入为词典和词云图保存位置
def wdcld(dic_name, fp):
    wc = WordCloud(
        font_path='simhei.ttf',
        max_words=80,
        background_color='white',
        width=960,
        height=600
    )
    wc.generate_from_frequencies(dic_name)
    plt.imshow(wc)
    # 消除坐标轴
    plt.axis("off")
    plt.show()
    wc.to_file(fp)


def main():
    with open(filename, encoding='utf-8') as f:

        random_segment()
        word_dic = word_frequency(ppcs(100000))

        print("词频统计结果为：", word_dic)
        feature = s_feature(word_dic)
        print("特征集为：", feature)
        # 过短&无意义弹幕过滤
        cln_danmu = clean(ppcs(10000))
        matrix = onehot_matrix(ob=cln_danmu, dic=feature)
        print(matrix)
        for i in range(80):
            co_simi = random_simi(ob=cln_danmu, oht=matrix)
            print("两弹幕余弦相似度为", co_simi)

        wdcld(word_dic, "wordcloud.jpg")


if __name__ == "__main__":
    main()


