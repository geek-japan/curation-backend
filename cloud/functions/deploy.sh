# gcloud functions deploy search --trigger-http --runtime=python39 --region asia-northeast1 --memory 512MB
gcloud functions deploy search_bigquery --trigger-http --runtime=python39 --region asia-northeast1 --memory 512MB
# gcloud functions deploy detail_demo --trigger-http --runtime=python39 --region asia-northeast1 --memory 512MB
gcloud functions deploy detail --trigger-http --runtime=python39 --region asia-northeast1 --memory 512MB
gcloud functions deploy fetch_articles --trigger-event google.pubsub.topic.publish --trigger-resource fetch-article-pubsub --runtime=python39 --region asia-northeast1 --memory 512MB --timeout=540s