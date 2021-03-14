import json
import random


def demo_fetchArticleDetail(request):
    # 適当な色を作成
    color = ''.join([random.choice('0123456789ABCDEF') for i in range(6)])

    # ランダムなテキストを作成(最大300文字の「あ」)
    characters = random.randrange(300)
    text = '記事の概要' + str(characters) + ''.join(["あ" for i in range(characters)])

    data = {
        "imageUrl": "https://via.placeholder.com/" + color + "/150",
        "abstract": text
    }

    return json.dumps(data, ensure_ascii=False)