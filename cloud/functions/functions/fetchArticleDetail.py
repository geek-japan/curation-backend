import json

import metadata_parser

PLACEHOLDER_IMAGE = "https://via.placeholder.com/150?text=No+Image"


def fetchArticleDetail(request):
    request_json = request.get_json()

    try:
        url = request_json['url']
    except TypeError as e:
        return json.dumps({"error": "url is not specified. Please use POST and JSON."})

    try:
        page = metadata_parser.MetadataParser(url=url, search_head_only=True)
        title = page.get_metadatas('title')
        image = page.get_metadatas('image')
        abstract = page.get_metadatas('description')
        data = {
            "title": title[0] if title else "(タイトルなし)",
            "imageUrl": image[0] if image else PLACEHOLDER_IMAGE,
            "abstract": abstract[0] if abstract else ""
        }
    except:
        data = {
            "title": "(タイトルなし)",
            "imageUrl": PLACEHOLDER_IMAGE,
            "abstract": ""
        }

    return json.dumps(data, ensure_ascii=False)
