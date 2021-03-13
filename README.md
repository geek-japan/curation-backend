# curation_system

## デプロイのための仕様

`cloud/`以下にデプロイ用のデータを置いています。

ここには、「Google Cloud Platform」でデプロイ可能な状態にした
`curation_system`を公開しています。

### 全体像

主に以下の部分で次のデプロイ方法を採用しています。

- バックエンドのPythonスクリプト: Cloud Functions
- 今までに取得したRSSのまとまり/(NewsAPIなどから取得した学習用データ) : BigQuery
- ダウンロードするRSSのURL/データの最終取得日 : Firebase Cloud Firestore
- 分類器本体(.pickle)/分類用の辞書(word/all_id2word.txt): Firebase Storage
- フロントエンド: Firebase Hosting

このうち、Firebase関係(Firestore, Storage, Hosting)は、
「firebase CLI」により管理されています。(`firebase.json`)

その他のGCP関係は「Deployment Manager」で管理する予定ですが、
現在のところ各ディレクトリにあるシェルスクリプト等で対応しています。

