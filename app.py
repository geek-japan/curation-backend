# バックエンドライブラリ
import os
from flask_cors import CORS
from flask import *
import pprint
#スクレイピング関連ライブラリ
import requests
from bs4 import BeautifulSoup
import re
import feedparser
import json
# 日付
import datetime

#　自作ライブラリ
import classify

# AI関連ライブラリ
from gensim.corpora import Dictionary
import pickle
import classify

#　使用ツールで主となる検索ワード
TARGET = '地方創生'

app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False

'''
リクエスト例
curl -X POST http://127.0.0.1:5000/search?from=2021/3/2&to=2021/3/3&q=福島県,農業,大学生
'''

def conditional_search(json_load,dt_from,dt_to):
    send = []
    for i in range(json_load['hit_number']):
        pub_date = json_load['results'][i]['published']
        tz = re.findall('T.*Z',pub_date)
        pub_date = pub_date.replace(tz[0],'')
        pub_date = datetime.datetime.strptime(pub_date, '%Y-%m-%d')
        # もしも期間内であったら追加
        if dt_from <= pub_date <= dt_to:
            send.append(json_load['results'][i])

    # フロント側が受け取りやすい形で出す
    result_format = {
        'hit_number': len(send),
        'results': send,
        'elapsed_days': 0
    }

    return result_format

@app.route('/')
def hello_world():
    return "Curation tool"

@app.route('/test', methods=['GET','POST'])
def test():

    q = ''
    FROM = ''
    TO = ''
    PREFCTURE = ''
    CATEGORY = ''
    # parameter: from,to,prefecture,city,category,q
    if request.args.get('from') is None:
        FROM = request.args.get('from')
    if request.args.get('to') is None:
        TO = request.args.get('to')
    if request.args.get('prefecture') is None:
        PREFCTURE = request.args.get('prefecture')
    if request.args.get('category') is None:
        CATEGORY = request.args.get('category')
    if request.args.get('q') is None:
        q = request.args.get('q')
        q = q.split(',')

    # URLの作成
    keywords = '{'
    # 地方創生は毎回入れる
    keywords += TARGET
    # キーワードを入れる
    for i in range(len(q)):
        keywords += ','
        keywords += q[i]
    # 期間がある場合は指定する
    keywords += '},after:'
    keywords += FROM
    keywords += '%20before:'
    keywords += TO
    urlName = "https://news.google.com/rss/search?&hl=ja&gl=JP&ceid=JP:ja&q="
    urlName += keywords

    # Googleで地方創生で検索（条件なども含めて）
    # urlnameに入ってくる例
    # urlname = https://news.google.com/rss/search?&hl=ja&gl=JP&ceid=JP:ja&q={地方創生,福島県,郡山市,農業},after:2019/7/29%20before:2019/8/30
    url = requests.get(urlName)
    soup = BeautifulSoup(url.content, "html.parser")
    elems = soup.find_all("item")
    # 取得した結果をいい感じに整形
    data = []
    for elem in elems: 
        # タイトルの抽出
        title = str(elem.find_all("title")).replace('[<title>','').replace('</title>]','')
        # リンクの抽出: リンク前半のreplace,リンク後半のreplaceでlinkを取得
        link = str(elem.find_all("description")).replace('[<description>&lt;a href="','')
        tmp = re.findall('" target.*</description>]',link)
        link = link.replace(tmp[0],'')
        # 結果挿入
        article = {'title':title,'link':link}
        data.append(article)

    # フロント側が受け取りやすい形で出す
    result_format = {
        'hit_number': len(data),
        'results': data
    }   
    return jsonify(
        result_format
    )

@app.route('/search', methods=['GET','POST'])
def search():
    #-- パラメーターを取得する --#
    q = ''
    FROM = ''
    TO = ''
    PREFCTURE = ''
    CATEGORY = ''
    # parameter: from,to,prefecture,city,category,q
    if request.args.get('from') is not None:
        FROM = request.args.get('from')
    if request.args.get('to') is not None:
        TO = request.args.get('to')
    if request.args.get('prefecture') is None:
        PREFCTURE = request.args.get('prefecture')
    if request.args.get('category') is None:
        CATEGORY = request.args.get('category')
    if request.args.get('q') is None:
        q = request.args.get('q')
        q = q.split(',')

    #-- 前回リクエスト時から現在までどれくらい時間が経過したか計算  --# 
    # 現在時刻
    dt_current = datetime.date.today()
    # log.txtから最終利用時刻を調べる
    with open('log.txt', mode='rb') as f:
        time = f.readline().decode()
        dt_previous = datetime.datetime.strptime(time, '%Y-%m-%d')

    # 期間指定のパラメーター
    dt_to = datetime.datetime.strptime(TO, '%Y/%m/%d')
    dt_from = datetime.datetime.strptime(FROM, '%Y/%m/%d')


    # 最終アクセスから一日以上経過してたら調べる
    td = dt_current - dt_previous.date()
    # 一日以上経過していたとき
    if td.days > 0:
        # 取得ニュースを格納する配列
        news_list = []
        # 各rssからニュースを取得
        json_open = open('rss.json', 'r')
        json_load = json.load(json_open)
        for i in json_load:
            rss_dic = feedparser.parse(json_load[i])
            entries_data = rss_dic.entries
            article = {}
            for j in (reversed(entries_data)):
                if 'title' in j:
                    article['title'] = j.title
                if 'link' in j:
                    article['link'] = j.link
                if 'published' in j:
                    article['published'] = j.published
            news_list.append(article)

        # 取得してきたニュースをレコメンドすべきか判断
        dct = Dictionary.load_from_text("word/all_id2word.txt")
        # モデルのオープン
        with open('model.pickle', mode='rb') as f:
            classifier = pickle.load(f)
        # Bowの作成
        bow_docs = classify.make_bow(dct)
        result = classify.predict(news_list,dct,classifier,bow_docs)

        # フロント側が受け取りやすい形で出す
        result_format = {
            'hit_number': len(result),
            'results': result,
            'elapsed_days': td.days
        }

        #　AIが推論した結果を条件付きで絞ることなく保存
        with open('result.json', mode='wb') as f:
            d = json.dumps(result_format)
            f.write(d.encode())

        # 最後にリクエストされた条件にマッチしたものに絞る
        curation_data = conditional_search(result_format,dt_from,dt_to)

                
    # 一日以内
    else:
        # 初回時に生成されたデータを読み込み
        json_open = open('./result.json', 'r')
        json_load = json.load(json_open)

        # 最後にリクエストされた条件にマッチしたものに絞る
        curation_data = conditional_search(json_load,dt_from,dt_to,)


    # 利用時刻を記録
    with open('log.txt', mode='wb') as f:
        f.write(str(dt_current).encode())

    return jsonify(
        curation_data
    )

@app.after_request
def after_request(response):
  response.headers.add('Access-Control-Allow-Origin', '*')
  response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
  response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
  return response

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)