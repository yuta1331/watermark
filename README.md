# watermark
匿名化データに透かしを入れる。

## Data
yuta1331/Anonymizerで作った匿名化データ

## How to
### preprocess
まずは`preprocess/`にgeocodingのためのデータ置く必要がある。<br>
今回は国交省の公開データを用いる。<br>
http://nlftp.mlit.go.jp/cgi-bin/isj/dls/_choose_method.cgi

これを`addr.csv`とする。

次に、`geomaker.py`を実行する。<br>
そうすると、`watermark/pickles/`に`addr2format.pkl`と`addr2geo.pkl`が作成される。
