from functions.searchArticles import search_articles
from functions.cors import run_function_with_cors_enabled
from functions.demo_fetchArticleDetail import demo_fetchArticleDetail

def search(request):
    return run_function_with_cors_enabled(request, search_articles)

def detail_demo(request):
    return run_function_with_cors_enabled(request, demo_fetchArticleDetail)