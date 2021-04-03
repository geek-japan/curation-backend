import datetime
import json

from google.cloud import bigquery
from pytz import timezone


def search_articles_bigquery(request):
    # 各種パラメータの取得・データ型の変換
    q = ''
    FROM = ''
    TO = ''
    PREFCTURE = ''
    NUMBER = 100
    PAGE = 1
    if request.args.get('from') is not None:
        FROM = request.args.get('from')
    if request.args.get('to') is not None:
        TO = request.args.get('to')
    if request.args.get('prefecture') is not None:
        PREFCTURE = request.args.get('prefecture')
    if request.args.get('q') is not None:
        q = request.args.get('q')
    if request.args.get('number') is not None:
        NUMBER = int(request.args.get('number'))
    if request.args.get('page') is not None:
        PAGE = int(request.args.get('page'))

    # 期間指定のパラメーター
    dt_from = datetime.datetime.strptime(FROM, '%Y/%m/%d').astimezone(timezone('Asia/Tokyo'))
    dt_to = datetime.datetime.strptime(TO, '%Y/%m/%d').astimezone(timezone('Asia/Tokyo')) + datetime.timedelta(days=1)

    client = bigquery.Client.from_service_account_json('.auth/curation-system-firebase-adminsdk.json')

    # 合計の件数を取得
    query = """
        SELECT COUNTIF((publishedAt BETWEEN  @date_from AND @date_to)
        AND STRPOS(CONCAT(title, description), @query) > 0
        AND STRPOS(CONCAT(title, description), @prefecture) > 0
        AND isLocalArticle = 1) AS result
        FROM `curation-system.news.news`
    """

    # BigQueryから必要な記事の抽出
    query_needed = """
      SELECT title, description, url, publishedAt, urlToImage, isLocalArticle
      FROM `curation-system.news.news`
      WHERE
       (publishedAt BETWEEN  @date_from AND @date_to)
      AND STRPOS(CONCAT(title, description), @query) > 0
      AND STRPOS(CONCAT(title, description), @prefecture) > 0
      AND isLocalArticle = 1
      ORDER BY publishedAt DESC
      LIMIT @number
      OFFSET @offset
    """

    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("query", "STRING", q),
            bigquery.ScalarQueryParameter("prefecture", "STRING", PREFCTURE),
            bigquery.ScalarQueryParameter("date_from", "TIMESTAMP", dt_from),
            bigquery.ScalarQueryParameter("date_to", "TIMESTAMP", dt_to),
            bigquery.ScalarQueryParameter("number", "INTEGER", NUMBER),
            bigquery.ScalarQueryParameter("offset", "INTEGER", NUMBER * (PAGE - 1))
        ]
    )

    query_job_sum = client.query(query, job_config=job_config)
    query_job = client.query(query_needed, job_config=job_config)

    # 結果を整形
    hit_number = 0
    for row in query_job_sum:
        hit_number = row["result"]

    news_list = []
    for row in query_job:
        news_list.append(
            {
              "title": row["title"],
              "link": row["url"],
              "published": row["publishedAt"].astimezone(timezone('Asia/Tokyo')).isoformat(),
              "description": row["description"]
            }
        )

    news_list_format = {
      'hit_number': hit_number,
      'current_articles': len(news_list),
      'page': PAGE,
      'results': news_list
    }

    return json.dumps(news_list_format, ensure_ascii=False)
