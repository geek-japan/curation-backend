# curation-backend

## Overview

「記事自動抽出システム」をWebアプリとして公開するためのバックエンドです。

- GCP上にデプロイ可能なシステム
- [curation-ai](https://github.com/geek-japan/curation-ai)の分類器によって地方創生に関する記事を抽出
- 内部でBigQueryを用いており過去の記事を高速に検索可能
- 期間指定・キーワード指定による記事検索が可能
- 定期的に自動で複数のRSSフィードから新規記事を取得

## システムの仕様

主に以下の部分で次のデプロイ方法を採用しています。

- バックエンドのPythonスクリプト: Cloud Functions
- 今までに取得したRSSのまとまり/(NewsAPIなどから取得した学習用データ) : BigQuery
- ダウンロードするRSSのURL/データの最終取得日 : Firebase Cloud Firestore
- 分類器本体(.pickle)/分類用の辞書(word/all_id2word.txt): Firebase Storage
- フロントエンド: Firebase Hosting

このうち、Firebase関係(Firestore, Storage, Hosting)は、
「firebase CLI」により管理されています。(`firebase.json`)

# How to Deploy

### 1. firebase部分のインストール

`cloud`ディレクトリ内で、`firebase deploy`を行ってください。

firebase経由でGCP上にFirestore及びStorageが作成されます。

### 2. Storageに必要ファイルのアップロード

`cloud/storage`にある`upload.sh`を実行してください。

`src`以下にある、推論用のAI(.pickle)やデータセット、記事の取得先RSSがクラウドにアップロードされます。

### 3. 新規記事取得APIの自動実行設定

fetch_articlesを自動実行するために、GCPのコンソールからCloud Schedulerを設定します。

まず、Pub/Subで`fetch-article-pubsub`トピックを作成します。

次に、Cloud Schedulerから次の内容のジョブを作成してください。

![image](https://user-images.githubusercontent.com/38032069/113497255-36ced380-953d-11eb-85c0-af6eba536f30.png)

### 4. API本体のデプロイ

`cloud/functions`にある`deploy.sh`を実行してください。

`src`以下にある、

- search_bigquery: 記事検索API
- detail: 記事情報(OGP)取得API
- fetch_articles: 新規記事取得API

がデプロイされます。

# Tips

## RSSの取得先の追加・削除について

Storageの`rss.json`を編集してください。

次回の新規記事取得時から、指定されたRSSの中身の記事が利用されます。

## フロントのデプロイについて

同じfirebaseのプロジェクト上でHostingにより行っています。

フロントのmainブランチにマージをした際に自動でデプロイされるようになっています。

詳しくは[curation-front](https://github.com/geek-japan/curation-front)の`firebase.json`やGitHub Actionsをご覧ください。

## BigQueryへの既存記事データ追加について

RSSから自動で記事を追加するようになっていますが、過去の記事などを手動で追加することもできます。

ここでは、お手持ちのCSVファイル等をBigQueryに追加する方法を説明します。

### 記事データの用意

予め、以下の内容でニュース記事データのCSVを作成しておいてください。

![image](https://user-images.githubusercontent.com/38032069/113496964-df7b3400-9539-11eb-9d80-e143d2c8e6d6.png)

全てのデータを埋める必要はありませんが、publishedAt、urlは必須項目です。また、現在のところ`isLocalArticle`が`1`のものを地域創生の記事として抽出していますので、[curation-maintenance](https://github.com/geek-japan/curation-maintenance/blob/main/CURATION_README.md)を参考に、このデータを追加してください。

### 記事データの反映

Storageのどこかに、用意したCSVファイルをアップロードします。

その後、BigQueryのコンソールで、`curation-system:news`データセットに対して、次のようにテーブルを作成してください。

エラーの許可数やジャグ行の許可は、利用するデータに応じて任意で設定してください。

![image](https://user-images.githubusercontent.com/38032069/113497014-73e59680-953a-11eb-80d0-9d92af2360a4.png)

