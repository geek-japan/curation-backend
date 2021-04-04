from functions.searchArticles import search_articles
from functions.cors import run_function_with_cors_enabled
from functions.demo_fetchArticleDetail import demo_fetchArticleDetail
from functions.fetchArticleDetail import fetchArticleDetail
from functions.searchArticlesBigQuery import search_articles_bigquery
from functions.crawlNewArticle import crawl_new_article

def search(request):
    return run_function_with_cors_enabled(request, search_articles)

def search_bigquery(request):
    return run_function_with_cors_enabled(request, search_articles_bigquery)

def detail(request):
    return run_function_with_cors_enabled(request, fetchArticleDetail)

def detail_demo(request):
    return run_function_with_cors_enabled(request, demo_fetchArticleDetail)

def fetch_articles(event, context):
    return crawl_new_article(context)