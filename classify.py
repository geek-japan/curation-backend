
from math import sqrt
from tqdm import tqdm
from sklearn.svm import SVC
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
from gensim.corpora import Dictionary
from gensim.models import word2vec
import numpy as np
import pandas as pd
import gensim
import gensim.parsing
import sys
from janome.tokenizer import Tokenizer
import preprocessing
import learning

num_topics = 2

def make_bow(dct):
    df = pd.read_csv('dataset/preprocessed/pre_mix_title.csv')
    bow_docs = {}
    bow_docs_all_zeros = {}
    for i in range(len(df)):
        word = df['title'][i].replace('[','').replace(']','').replace("'",'')
        word = word.split(',')
        sparse = dct.doc2bow(word)
        
        if i <= 99:
            bow_docs['local_{}'.format(i)] = sparse
            dense = learning.vec2dense(sparse, num_terms=len(dct))
            bow_docs_all_zeros['local_{}'.format(i)] = all(d == 0 for d in dense)
        else :
            bow_docs['global_{}'.format(i)] = sparse
            dense = learning.vec2dense(sparse, num_terms=len(dct))
            bow_docs_all_zeros['global_{}'.format(i)] = all(d == 0 for d in dense)
    return bow_docs

def predict(target,dct,classifier,bow_docs):

    lsi_model = gensim.models.LsiModel(
        bow_docs.values(),
        id2word=dct,
        num_topics=num_topics
    )

    # ストップワードの読み込み
    with open('word/Japanese.txt') as fd:
        stop_words = frozenset(fd.read().splitlines())

    send = []
    t = Tokenizer()
    for i in range(len(target)):
        article_target = preprocessing.preprocessing(target[i]['title'],stop_words,t)
        sparse = dct.doc2bow(article_target)
        sparse= lsi_model[sparse]
        dense = learning.vec2dense(sparse, num_topics)
        norm = sqrt(sum(num**2 for num in dense))
        #unit_vec = [num / norm for num in dense]
        unit_vec = [np.divide(num, norm, out=np.zeros_like(num), where=num!=0) for num in dense]

        if np.isnan(unit_vec[0]):
            unit_vec[0] = 0
            unit_vec[1] = 0
        pre =[]
        pre.append(unit_vec)

        # 推論
        ans = classifier.predict(pre)
        if ans[0] == 1:
            send.append(target[i])

    return  send

def main():
    target = 'PTA連合会でも使途不明金 「極めて遺憾」会長の河村元官房長官'

    dct = Dictionary.load_from_text("word/all_id2word.txt")
    bow_docs = make_bow(dct)

    lsi_model = gensim.models.LsiModel(
        bow_docs.values(),
        id2word=dct.load_from_text('word/all_id2word.txt'),
        num_topics=num_topics
    )

    target = preprocessing.preprocessing(target)
    sparse = dct.doc2bow(target)
    sparse= lsi_model[sparse]
    dense = learning.vec2dense(sparse, num_topics)
    norm = sqrt(sum(num**2 for num in dense))
    unit_vec = [num / norm for num in dense]

    if np.isnan(unit_vec[0]):
        unit_vec[0] = 0
        unit_vec[1] = 0
    pre =[]
    pre.append(unit_vec)

    # モデルのオープン
    with open('model.pickle', mode='rb') as f:
        classifier = pickle.load(f)
    ans = classifier.predict(pre)
    print(ans[0])

if __name__ == "__main__":
    main()