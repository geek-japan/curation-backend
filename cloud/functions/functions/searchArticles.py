import json
import pickle
import datetime
import feedparser
from gensim.corpora import Dictionary
from .core.classify import make_bow, predict
from .core.conditional_search import conditional_search
from .core.cloudstorage import upload_blob, download_blob


def search_articles(request):
    # -- パラメーターを取得する --#
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

    # -- 前回リクエスト時から現在までどれくらい時間が経過したか計算  --#
    # 現在時刻
    dt_current = datetime.date.today()
    # log.txtから最終利用時刻を調べる
    download_blob('log.txt', '/tmp/log.txt')
    with open('/tmp/log.txt', mode='rb') as f:
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
        download_blob('rss.json', '/tmp/rss.json')
        json_open = open('/tmp/rss.json', 'r')
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

        # テスト用にすべての記事も保存
        with open('/tmp/result-all.json', mode='wb') as f:
            d = json.dumps(news_list)
            f.write(d.encode())
        upload_blob('/tmp/result-all.json', 'result-all.json')

        # 取得してきたニュースをレコメンドすべきか判断
        download_blob('word/all_id2word.txt', '/tmp/all_id2word.txt')
        dct = Dictionary.load_from_text("/tmp/all_id2word.txt")
        # モデルのオープン
        download_blob('model.pickle', '/tmp/model.pickle')
        with open('/tmp/model.pickle', mode='rb') as f:
            classifier = pickle.load(f)
        # Bowの作成
        bow_docs = make_bow(dct)
        result = predict(news_list, dct, classifier, bow_docs)

        # フロント側が受け取りやすい形で出す
        result_format = {
            'hit_number': len(result),
            'results': result,
            'elapsed_days': td.days
        }

        # 　AIが推論した結果を条件付きで絞ることなく保存
        with open('/tmp/result.json', mode='wb') as f:
            d = json.dumps(result_format)
            f.write(d.encode())
        upload_blob('/tmp/result.json', 'result.json')

        # 最後にリクエストされた条件にマッチしたものに絞る
        curation_data = conditional_search(result_format, dt_from, dt_to)

    # 一日以内
    else:
        # 初回時に生成されたデータを読み込み
        download_blob('result.json', '/tmp/result.json')
        json_open = open('/tmp/result.json', 'r')
        json_load = json.load(json_open)

        # 最後にリクエストされた条件にマッチしたものに絞る
        curation_data = conditional_search(json_load, dt_from, dt_to, )

    # 利用時刻を記録
    with open('/tmp/log.txt', mode='wb') as f:
        f.write(str(dt_current).encode())
    upload_blob('/tmp/log.txt', 'log.txt')

    return json.dumps(curation_data, ensure_ascii=False)
