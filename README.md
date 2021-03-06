# watermark
匿名化データに透かしを入れる。

## Data
yuta1331/Anonymizerで作った匿名化データ<br>
`csvs/anonymized_data.csv`として保存。

## How to
### preprocess
まずは`preprocess/`にgeocodingのためのデータ置く必要がある。<br>
今回は国交省の公開データを用いる。<br>
http://nlftp.mlit.go.jp/cgi-bin/isj/dls/_choose_method.cgi

これを`addr.csv`とする。

次に、`geomaker.py`を実行する。<br>
そうすると、`pickles/`に`addr2format.pkl`と`addr2geo.pkl`が作成される。

### configuration
watermarkingとdetectingの共通設定は`consts.py`にて。

### run watermarking
`anonymized_data.csv`にwatermarkを入れて`watermarked_data.csv`を生成する。

watermarking固有の設定はmain.pyのconfig欄で。

```bash
python main.py
```

実行後、`csvs/watermarked_data.csv`が保存される。

### run detecting
`anonymized_data.csv`と`watermarked_data.csv`を用いて埋め込まれたbitを検出する。

```bash
python main_detect.py
```

## Caution
現在の実装はデータの各行末にシーケンシャルナンバーがないとちゃんと動作しない。
属性名はseq。
理由は評価のため。

最終的には、seqがなくても動作できるようにする予定。
