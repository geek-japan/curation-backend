# news.sqlite3 について

記事数が多く、地方の記事が取得できなくなることを避けるため、東京・大阪・愛知の記事は抜いてあります。

# 実行例

```
[fetch] 東京 2017-11-21 2017-11-23 66
[ok] 3696 6556
[ex] ('第17回 おとなの悟り婚 12/2 14時 in池袋 ～清き出会いと清き幸せ～ 写仏編', '満足度の大変高い【特別企画】パーティー★。おとなの悟り婚。～清き出会いと清き幸せ～ 写仏編。 。 …', datetime.datetime(2017, 11, 21, 9, 20, 10, tzinfo=<DstTzInfo 'Asia/Tokyo' JST+9:00:00 STD>), 'https://machicon.jp/events/OwaxRh/', 'Machicon.jp', 'OTOCON（おとコン）', 'https://machicon.jp/uploads/event/eyecatch/1674117/f9d25ebf01aa122dcddb.jpg', '東京')

[fetch] 東京 2017-11-21 2017-11-23 67
[ok] 0 6556

[fetch] 東京 2017-11-24 2017-11-26 1
[ok] 100 4808
[ex] ('株式会社アイモバイルアイモバイル、最新版Safari ブラウザのトラッキング防止機能 ITPに対応', '株式会社アイモバイル（本社：東京都渋谷区、代表取締役社長：野口哲也、東証マザーズ上場：証券コード6535、以下「アイモバイル」）はスマートフォン・PCのアドネットワーク「i-mobile」において、Apple 社が追加した Safari ブラウザのトラッキング防止機能 Intelligent Tracking Prevention（以下、ITP）(※1)への対応...', datetime.datetime(2017, 11, 27, 9, 0, tzinfo=<DstTzInfo 'Asia/Tokyo' JST+9:00:00 STD>), 'https://japan.cnet.com/release/30220471/', 'CNET', None, 'https://japan.cnet.com/media/c/2012/images/logo/logo_horizontal.jpg', '東京')

```
