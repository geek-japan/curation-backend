from functions.searchArticles import search_articles
from flask import make_response

def search(request):
    return make_response(search_articles(request), 200)