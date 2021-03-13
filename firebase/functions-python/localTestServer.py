from flask import Flask, request
from functions.searchArticles import search_articles

app = Flask(__name__)

@app.route('/search', methods=['GET'])
def search():
    return search_articles(request)


if __name__ == '__main__':
    app.run()
