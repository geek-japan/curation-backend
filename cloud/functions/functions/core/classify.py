from math import sqrt
from gensim.corpora import Dictionary
from gensim.models import word2vec
import numpy as np
import pandas as pd
import gensim
import gensim.parsing
from janome.tokenizer import Tokenizer
from . import preprocessing
from . import learning
from .cloudstorage import download_blob

num_topics = 4


def make_bow(dct):
    download_blob('dataset/preprocessed/pre_tokenized.csv', '/tmp/pre_tokenized.csv')
    df = pd.read_csv('/tmp/pre_tokenized.csv')
    bow_docs = {}
    bow_docs_all_zeros = {}
    for i in range(len(df)):
        word = df['title'][i].replace('[', '').replace(']', '').replace("'", '')
        word = word.split(',')
        sparse = dct.doc2bow(word)

        if df['tag'][i] == 1:
            bow_docs['local_{}'.format(i)] = sparse
            dense = learning.vec2dense(sparse, num_terms=len(dct))
            bow_docs_all_zeros['local_{}'.format(i)] = all(d == 0 for d in dense)
        else:
            bow_docs['global_{}'.format(i)] = sparse
            dense = learning.vec2dense(sparse, num_terms=len(dct))
            bow_docs_all_zeros['global_{}'.format(i)] = all(d == 0 for d in dense)
    return bow_docs


def predict(target, dct, classifier, bow_docs):
    lsi_model = gensim.models.LsiModel(
        bow_docs.values(),
        id2word=dct,
        num_topics=num_topics
    )

    stop_words = None
    # ストップワードの読み込み
    download_blob('dataset/preprocessed/pre_mix_title.csv', '/tmp/pre_mix_title.csv')
    with open('/tmp/pre_mix_title.csv') as fd:
        stop_words = frozenset(fd.read().splitlines())

    send = []
    t = Tokenizer()
    pre = []
    print(len(target))
    for i in range(len(target)):
        article_target = preprocessing.preprocessing(target[i]['title'] + ' ' + target[i]['description'], stop_words, t)
        sparse = dct.doc2bow(article_target)
        sparse = lsi_model[sparse]
        dense = learning.vec2dense(sparse, num_topics)
        norm = sqrt(np.sum(num ** 2 for num in dense))
        # unit_vec = [num / norm for num in dense]
        unit_vec = [np.divide(num, norm, out=np.zeros_like(num), where=num != 0) for num in dense]
        if np.isnan(unit_vec[0]):
            for j in range(num_topics):
                unit_vec[j] = 0
        pre.append(unit_vec)
    # 推論
    ans = classifier.predict(pre)
    print(ans)
    for i in range(len(ans)):
        if ans[i] == 1:
            send.append(target[i])
    print(send)
    return send

