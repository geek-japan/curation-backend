import sys
import pandas as pd
from janome.tokenizer import Tokenizer
import gensim
from sklearn.svm import SVC
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
from gensim.corpora import Dictionary
from gensim.models import word2vec
import cython
import numpy as np
from tqdm import tqdm
from math import sqrt
import pickle
import re
import copy

# コサイン類似度の閾値
COS_NUM = 0.85

# トピック数
num_topics = 2

def cos_sim(v1, v2):
    return np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2))

def vec2dense(vec, num_terms):
    '''Convert from sparse gensim format to dense list of numbers'''
    return list(gensim.matutils.corpus2dense([vec], num_terms=num_terms).T[0])

def main():
    # コマンドラインからファイル名を取得 (csvのみ)
    FILENAME = sys.argv[1] 

    # 前処理するデータの読み込み
    df = pd.read_csv('dataset/preprocessed/'+FILENAME)

    #--- 類似キーワードの集約 ---#

    for i in range(len(df)):
        word = df['title'][i].replace('[','').replace(']','').replace("'",'')
        word = word.split(',')

    dct_words = []
    for i in range(len(df)):
        for j in range(len(word)):
            dct_words.append(word[j])
    #　ユニークなキーワードのみにする       
    dct_words = list(set(dct_words))

    # モデルのロード
    model = word2vec.Word2VecVocab.load('w2v_model/chive-1.2-mc5.kv')
    #model = gensim.models.KeyedVectors.load_word2vec_format('/model/model.vec', binary=False)

    # 全ての組み合わせの計算結果を保存する
    # 類似キーワードの算出中 
    calc_data = {}
    for i in tqdm(range(len(dct_words))):
        for j in range(i+1,len(dct_words)):
            try:
                a = model[dct_words[i]]
                b = model[dct_words[j]]
            except KeyError:
                continue
            rate = cos_sim(a,b)
            calc_data[(i,j)] = rate

    sorted_data = sorted(calc_data.items(), reverse =True, key= lambda x: x[1])

    # コサイン類似度
    # 閾値を超えた件数をカウントする
    top_num= 0
    for i in range(len(sorted_data)):
        if sorted_data[i][1] < COS_NUM:
            top_num= i
            break

    # 置換するキーワードを対応させる
    replace_dic = {}
    # 一回辞書を作ってしまう
    for i in range(len(dct_words)):
        replace_dic[dct_words[i]] = dct_words[i]
    # 置き換える必要のあるところだけ変える
    for i in range(top_num):
        replace_dic[dct_words[sorted_data[i][0][1]]] = dct_words[sorted_data[i][0][0]]   

    # df内のキーワードを置き換える
    for i in range(len(df)):
        for j in range(df['len'][i]):
            text = replace_dic[df['title'][i][j]]
            if df['title'][i][j] != text:
                df['title'][i][j] = text

    #--- 特徴語の抽出 ---#

    # 辞書を作成
    # 低頻度と高頻度のワードは除く
    dct = gensim.corpora.Dictionary(df['title'])
    unfiltered = dct.token2id.keys()
    dct.filter_extremes(no_below=12 ,no_above=4)
    filtered = dct.token2id.keys()
    filtered_out = set(unfiltered) - set(filtered)

    #print("特徴語")
    #print(dct.token2id.keys(), "(%d words)" % len(dct.token2id.keys()), '\n')   

    # 辞書を保存
    dct_txt = "word/all_id2word.txt"
    dct.save_as_text(dct_txt)

    #--- Bag of Wordsベクトルの作成 ---#
    bow_docs = {}
    bow_docs_all_zeros = {}
    for i in range(len(df)):
        sparse = dct.doc2bow(df['title'][i])
        
        if df_wakati['tag'][i] == 1:
            bow_docs['local_{}'.format(i)] = sparse
            dense =vec2dense(sparse, num_terms=len(dct))
            bow_docs_all_zeros['local_{}'.format(i)] = all(d == 0 for d in dense)
        else :
            bow_docs['global_{}'.format(i)] = sparse
            dense =vec2dense(sparse, num_terms=len(dct))
            bow_docs_all_zeros['global_{}'.format(i)] = all(d == 0 for d in dense)
    
    #--- Bag of Wordsベクトルの次元削減 ---#
    lsi_docs = {}
    lsi_model = gensim.models.LsiModel(
        bow_docs.values(),
        id2word=dct.load_from_text('word/id2word.txt'),
        num_topics=num_topics
    )

    for i in range(len(df)):
        if df_wakati['tag'][i] == 1:
            vec = bow_docs['local_{}'.format(i)]
            sparse = lsi_model[vec]
            dense = vec2dense(sparse, num_topics)
            lsi_docs['local_{}'.format(i)] = sparse
        else:
            vec = bow_docs['global_{}'.format(i)]
            sparse = lsi_model[vec]
            dense = vec2dense(sparse, num_topics)
            lsi_docs['global_{}'.format(i)] = sparse

    #--- データの正規化 ---#
    unit_vecs = {}
    for i in range(len(df)):
        if  df_wakati['tag'][i] == 1:
            vec = vec2dense(lsi_docs['local_{}'.format(i)], num_topics)
            norm = sqrt(np.sum(num**2 for num in vec))
            unit_vec = [num / norm for num in vec]
            if np.isnan(unit_vec[0]):
                for j in range(num_topics):
                    unit_vec[j] = 0
            unit_vecs['local_{}'.format(i)] = unit_vec
        else:
            vec = vec2dense(lsi_docs['global_{}'.format(i)], num_topics)
            norm = sqrt(np.sum(num**2 for num in vec))
            unit_vec = [num / norm for num in vec]
            if np.isnan(unit_vec[0]):
                for j in range(num_topics):
                    unit_vec[j] = 0
            unit_vecs['global_{}'.format(i)] = unit_vec

    #--- SVMによる学習と２クラス分類 ---#
    names = []
    for i in range(len(df)):
        if df_wakati['tag'][i] == 1:
            names.append('local_{}'.format(i))
        else:
            names.append('global_{}'.format(i))

    # 2クラス分類
    all_data = [unit_vecs[name] for name in names if re.match("local", name)]
    all_data.extend([unit_vecs[name] for name in names
                    if re.match("global", name)])

    all_labels = [1 for name in names if re.match("local", name)]
    all_labels.extend([2 for name in names if re.match("global", name)])

    train_data, test_data, train_label, test_label = train_test_split(all_data,all_labels)

    # SVMの学習
    classifier = SVC()
    classifier.fit(train_data, train_label)

    # 予測
    predict_label = classifier.predict(test_data)

    target_names = ["class 'local'", "class 'global'"]
    #print(classification_report(test_label, predict_label,target_names=target_names))

    with open('model.pickle', mode='wb') as fp:
        pickle.dump(classifier, fp)


if __name__ == "__main__":
    main()