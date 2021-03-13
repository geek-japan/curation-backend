import sys
import pandas as pd
from janome.tokenizer import Tokenizer

def preprocessing(pre_sentence,stop_words,t): #前処理をする関数
    #分かち書き形式にする
    wakati = [
        token.surface for token in t.tokenize(pre_sentence)
            if ((token.part_of_speech.split(',')[0] in ['形容詞', '副詞','名詞',]) or
    ((token.part_of_speech.split(',')[0] in ['動詞']) & (token.part_of_speech.split(',')[1] not in ['接尾'])))
    ]
    #ストップワードを除去する
    post_sentence = list(filter(lambda x: x not in stop_words, wakati))
    return post_sentence


def main():
    # コマンドラインからファイル名を取得 (csvのみ)
    FILENAME = sys.argv[1] 

    # 前処理するデータの読み込み
    df = pd.read_csv('dataset/original/'+FILENAME)

    t = Tokenizer()
    wakati = [] # 分かち書きしたタイトルを入れるための変数
    length = [] # １タイトルに含まれるキーワードの数を入れる

    # df内のデータを全て分かち書きする
    for i in range(len(df)):
        tmp = df['title'][i]
        tmp = [
            token.surface for token in t.tokenize(tmp)
            if ((token.part_of_speech.split(',')[0] in ['形容詞', '副詞','名詞',]) or
            ((token.part_of_speech.split(',')[0] in ['動詞']) & (token.part_of_speech.split(',')[1] not in ['接尾'])))
        ]
        length.append(len(tmp))
        wakati.append(tmp)

    df_wakati = pd.DataFrame({"title":wakati,"len":length})
    df_wakati.to_csv("dataset/preprocessed/pre_"+FILENAME)


if __name__ == "__main__":
    main()