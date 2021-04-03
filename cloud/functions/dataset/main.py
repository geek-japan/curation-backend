import calendar
import datetime
import sqlite3
import os

import pytz
import requests

REQUEST_BASE_URL = 'https://newsapi.org/v2/everything'
NEWSAPI_KEY = os.environ['NEWSAPI_KEY']

PREF_LIST = [
    '北海道',
    '青森',
    '岩手',
    '宮城',
    '秋田',
    '山形',
    '福島',
    '茨城',
    '栃木',
    '群馬',
    '埼玉',
    '千葉',
    # '東京',
    '神奈川',
    '新潟',
    '富山',
    '石川',
    '福井',
    '山梨',
    '長野',
    '岐阜',
    '静岡',
    '愛知',
    '三重',
    '滋賀',
    '京都',
    '大阪',
    '兵庫',
    '奈良',
    '和歌山',
    '鳥取',
    '島根',
    '岡山',
    '広島',
    '山口',
    '徳島',
    '香川',
    '愛媛',
    '高知',
    '福岡',
    '佐賀',
    '長崎',
    '熊本',
    '大分',
    '宮崎',
    '鹿児島',
    '沖縄'
]

# TEST.dbを作成する
# すでに存在していれば、それにアスセスする。
dbname = 'news.sqlite3'
conn = sqlite3.connect(dbname)

# sqliteを操作するカーソルオブジェクトを作成
cur = conn.cursor()

# 一ヶ月おきの感覚で繰り返し
end = datetime.datetime.strptime('2021-03-17', '%Y-%m-%d').date()
for n in range(6): # 180
    start = end + datetime.timedelta(days=-7)
    end = end + datetime.timedelta(days=-1)

    # 各都道府県ごとに取得
    for prefecture in PREF_LIST:
        # その月の最後の記事が取れるまで繰り返す
        page = 1
        while True:
            # newsAPIから情報取得
            params = {
                'q': '"' + prefecture + '"',
                'language': 'jp',
                'pageSize': 100,
                'from': start,
                'to': end,
                'sortBy': 'publishedAt',
                'apiKey': NEWSAPI_KEY,
                'page': page
            }

            print("[fetch]", prefecture, start, end, page)
            response = requests.get(REQUEST_BASE_URL, params)
            response_json = response.json()
            print("[ok]", len(response_json['articles']) * page, response_json['totalResults'])

            # print(response_json)

            if len(response_json['articles']) == 0:
                print()
                break

            exec_articles = []
            for article in response_json['articles']:
                # タイムゾーンを日本時間に
                dt = datetime.datetime.strptime(article['publishedAt'], '%Y-%m-%dT%H:%M:%SZ')
                dt = pytz.utc.localize(dt).astimezone(pytz.timezone("Asia/Tokyo"))

                exec_articles.append(
                    (article['title'], article['description'],
                     dt, article['url'],
                     article['source']['name'],
                     article['author'], article['urlToImage'], prefecture)
                )

            cur.executemany('INSERT INTO news VALUES (?,?,?,?,?,?,?,?)', exec_articles)
            # データベースへコミット。これで変更が反映される。
            conn.commit()

            print("[ex]", exec_articles[0])
            print()
            page = page + 1

            if page == 100:
                print("[warn] too many articles. 10000+ articles is ignored")

            if page * 100 >= response_json['totalResults']:
                break

    # その期間をすべて取れたら次の月へ
    end = start

# データベースへのコネクションを閉じる。(必須)
conn.close()
