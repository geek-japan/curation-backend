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
    if request.args.get('from') is not None:
        FROM = request.args.get('from')
    if request.args.get('to') is not None:
        TO = request.args.get('to')
    if request.args.get('prefecture') is None:
        PREFCTURE = request.args.get('prefecture')
    if request.args.get('q') is None:
        q = request.args.get('q')

    # 期間指定のパラメーター
    dt_from = datetime.datetime.strptime(FROM, '%Y/%m/%d').astimezone(timezone('Asia/Tokyo'))
    dt_to = datetime.datetime.strptime(TO, '%Y/%m/%d').astimezone(timezone('Asia/Tokyo')) + datetime.timedelta(days=1)

    # BigQueryから必要な記事の抽出 (AIは最後)
    client = bigquery.Client.from_service_account_json('.auth/curation-system-firebase-adminsdk.json')
    query = """
      SELECT title, description, url, publishedAt, urlToImage
      FROM `curation-system.news.news`
      WHERE
       (publishedAt BETWEEN  @date_from AND @date_to)
      AND STRPOS(CONCAT(title, description), @query) > 0
      AND STRPOS(CONCAT(title, description), @prefecture) > 0
      LIMIT 10
  """

    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("query", "STRING", q),
            bigquery.ScalarQueryParameter("prefecture", "STRING", PREFCTURE),
            bigquery.ScalarQueryParameter("date_from", "TIMESTAMP", dt_from),
            bigquery.ScalarQueryParameter("date_to", "TIMESTAMP", dt_to)
        ]
    )
    query_job = client.query(query, job_config=job_config)

    # 結果を整形
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
      'hit_number': len(news_list),
      'results': news_list
    }

    return json.dumps(news_list_format, ensure_ascii=False)
