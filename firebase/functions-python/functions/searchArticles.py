import json
import pickle
import datetime
import feedparser
from gensim.corpora import Dictionary
from .core.classify import make_bow, predict
from .core.conditional_search import conditional_search


def search_articles(request):

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
    # with open('log.txt', mode='rb') as f:
    #     time = f.readline().decode()
    #     dt_previous = datetime.datetime.strptime(time, '%Y-%m-%d')

    # 期間指定のパラメーター
    dt_to = datetime.datetime.strptime(TO, '%Y/%m/%d')
    dt_from = datetime.datetime.strptime(FROM, '%Y/%m/%d')


    # 最終アクセスから一日以上経過してたら調べる
    # td = dt_current - dt_previous.date()
    days = 1
    # 一日以上経過していたとき
    if days > 0:
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
        bow_docs = make_bow(dct)
        result = predict(news_list,dct,classifier,bow_docs)

        # フロント側が受け取りやすい形で出す
        result_format = {
            'hit_number': len(result),
            'results': result,
           # 'elapsed_days': td.days
        }

        #　AIが推論した結果を条件付きで絞ることなく保存
        # with open('result.json', mode='wb') as f:
        #     d = json.dumps(result_format)
        #     f.write(d.encode())

        # 最後にリクエストされた条件にマッチしたものに絞る
        curation_data = conditional_search(result_format, dt_from, dt_to)
        return json.dumps(curation_data, ensure_ascii=False)
    # # リクエスト本文からjsonを取得
    # request_json = request.get_json()
    # # クエリ文字列を取得
    # if request.args and 'name' in request.args:
    #     request_name = request.args.get('name')
    # # jsonから条件を取得
    # elif request_json and 'name' in request_json:
    #     request_name = request_json['name']
    # else:
    #     request_name = ''
    #
    # db = firestore.Client()
    #
    # # whereでdocument内の条件に一致するデータを取得
    # query = db.collection('user').where('name', '==', request_name)
    # docs = query.get()
    # users_list = []
    # for doc in docs:
    #     users_list.append(doc.to_dict())
    # return_json = json.dumps({"users": users_list}, ensure_ascii=False)
    # return return_json