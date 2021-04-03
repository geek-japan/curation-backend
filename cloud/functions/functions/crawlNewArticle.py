import datetime
import json
import pickle
import time
import numpy

import feedparser
import re

import metadata_parser
from dateutil.parser import parse
from gensim.corpora import Dictionary

from .core.classify import make_bow, predict
from .core.cloudstorage import upload_blob, download_blob
from google.cloud import bigquery

PLACEHOLDER_IMAGE = "https://via.placeholder.com/150?text=No+Image"
client = bigquery.Client.from_service_account_json('.auth/curation-system-firebase-adminsdk.json')
schema = [
    bigquery.SchemaField("ID", "STRING", mode="NULLABLE"),
    bigquery.SchemaField("title", "STRING", mode="NULLABLE"),
    bigquery.SchemaField("description", "STRING", mode="NULLABLE"),
    bigquery.SchemaField("publishedAt", "TIMESTAMP", mode="REQUIRED"),
    bigquery.SchemaField("url", "STRING", mode="REQUIRED"),
    bigquery.SchemaField("source", "STRING", mode="NULLABLE"),
    bigquery.SchemaField("author", "STRING", mode="NULLABLE"),
    bigquery.SchemaField("urlToImage", "STRING", mode="NULLABLE"),
    bigquery.SchemaField("isLocalArticle", "STRING", mode="NULLABLE")
]


def crawl_new_article(request):
    news_list = get_current_news_article()

    # 取得してきたニュースをレコメンドすべきか判断
    download_blob('word/all_id2word.txt', '/tmp/all_id2word.txt')
    dct = Dictionary.load_from_text("/tmp/all_id2word.txt")

    download_blob('model_2.pickle', '/tmp/model_2.pickle')
    with open('/tmp/model_2.pickle', mode='rb') as f:
        classifier = pickle.load(f)

    bow_docs = make_bow(dct)
    result = predict(news_list, dct, classifier, bow_docs)

    upsert_new_articles(result)

    return {"status": "ok"}


def upsert_new_articles(news_list):
    temp_table_id = create_temp_table()
    insert_news_list(temp_table_id, news_list)

    query = """
        MERGE
          `curation-system.news.news` AS T
        USING
          `curation-system.news.temp` AS S
        ON
          T.url = S.url
        WHEN NOT MATCHED THEN
          INSERT (ID, title, description, publishedAt, url, source, author, urlToImage, isLocalArticle)
          VALUES (ID, title, description, publishedAt, url, source, author, urlToImage, isLocalArticle)
    """
    client.query(query)
    client.delete_table(temp_table_id, not_found_ok=True)  # Make an API request.


class type_encoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, numpy.integer):
            return int(obj)
        elif isinstance(obj, numpy.floating):
            return float(obj)
        elif isinstance(obj, numpy.ndarray):
            return obj.tolist()
        else:
            return super(type_encoder, self).default(obj)

def insert_news_list(temp_table_id, news_list):
    with open("/tmp/news_list.jsonl", "wt", newline="") as f:
        for news in news_list:
            f.write(json.dumps(news, ensure_ascii=False, cls = type_encoder) + "\n")

    job_config = bigquery.LoadJobConfig(source_format=bigquery.SourceFormat.NEWLINE_DELIMITED_JSON,
                                        schema=schema, max_bad_records=10)
    with open('/tmp/news_list.jsonl', 'rb') as source_file:
        job = client.load_table_from_file(source_file, temp_table_id, job_config=job_config)
    job.result()

def create_temp_table():
    table_id = "curation-system.news.temp"

    table = bigquery.Table(table_id, schema=schema)
    client.create_table(table, exists_ok=True)  # Make an API request.
    return table_id


def get_current_news_article():
    news_list = []
    url_list = []
    # 各rssからニュースを取得
    download_blob('rss.json', '/tmp/rss.json')
    json_open = open('/tmp/rss.json', 'r')
    json_load = json.load(json_open)
    for i in json_load:
        print(json_load[i])
        rss_dic = feedparser.parse(json_load[i])
        entries_data = rss_dic.entries
        for j in (reversed(entries_data)):
            article = {}
            if 'title' in j:
                article_title = j.title
                # メディア名の削除
                article_title = re.sub("\(.+?\)", "", article_title)
                article['title'] = article_title
            if 'link' in j:
                article['url'] = j.link
            if 'published' in j:
                article['publishedAt'] = parse(j.published).strftime("%Y-%m-%d %H:%M:%S")
            if 'description' in j:
                article['description'] = j.description

            # 今までに存在したURLなら無視
            if article['url'] in url_list:
                continue
            url_list.append(article['url'])

            # 情報が少なく、ogpにより詳細が取れる場合は取得
            try:
                if article['description'] == "":
                    print('ogp used')
                    page = metadata_parser.MetadataParser(url=article['url'], search_head_only=True)
                    title = page.get_metadatas('title')
                    image = page.get_metadatas('image')
                    abstract = page.get_metadatas('description')
                    article['title'] = title[0] if title else article['title']
                    article['urlToImage'] = image[0] if image else PLACEHOLDER_IMAGE
                    article['description'] = abstract[0] if abstract else ""
                    time.sleep(1)  # 叩きすぎると怒られるので
            except metadata_parser.NotParsable as e:
                print(e)
            news_list.append(article)

    return news_list
