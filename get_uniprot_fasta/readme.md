# UniProtAPIを利用して、EntryIDリストからアミノ酸配列を取得
UniProtからタンパク質のアミノ酸配列を取得する際、少数であればブラウザ機能を利用したダウンロードが便利であるが、複数のタンパク質の配列をダウンロードする際にはAPIを利用した方が便利である。
APIを利用する際、任意の条件（例えばヒトのキュレーション済みタンパク質）でフィルタリングされるタンパク質を一斉にダウンロードする方法は公式HPに説明がされている一方、「EntryIDで指定したタンパク質のアミノ酸配列を一斉にダウンロード」する方法は公開されていない。

## 少数の配列の場合
少数の配列（例えば1000以下）であれば、EntryIDを１列に並べたテキスト`id_list.txt`を指定してWhile文で繰り返しダウンロードするのが便利である。
```
while read acc; do curl -sS "https://rest.uniprot.org/uniprotkb/${acc}.fasta"; done < id_list.txt > output.fasta
```
curlの`-s`オプションは進捗状況の表示を非表示にするオプションであり、`-S`はエラーを表示するオプションである。

## 多数の場合
上記の手法では、１エントリーごとにUniProtのWEBページにアクセスをするため、ダウンロードに時間がかかったりサーバー側に負荷がかかってしまう。
より多数のタンパク質配列をダウンロードする際には、UniProtが用意するstreamという大量データをダウンロードするのに特化したエンドポイントを利用する。
この目的で用意したスクリプトget_uniprot_fasta.shの使い方は以下のとおりである。
```
bash get_uniprot_fasta.sh id_list.txt output.fasta
```
`download_id.txt`にはダウンロードしたいタンパク質のEntryIDを１列に並べたテキストファイル
`download_protein.fasta`には出力として用いたいファイル名
をそれぞれ指定する。指定しなければ`id_list.txt`, `output.fasta`として認識される。

### スクリプトの解説
このコードの大枠としては、ダウンロードしたい配列のEntryIDをORで繋いでUniProtのstreamエンドポイントからダウンロードを実施している。
例えば、ACC1, ACC2, ACC3をEntryIDに持つタンパク質をダウンロードしたい場合は
```
curl -sS "https://rest.uniprot.org/uniprotkb/stream?format=fasta&query=(accession:ACC1%20OR%%20ACC2%20%ACC3)"
```
というようにaccessionの引数にORで繋いで指定をしている。ORの前後の`%20%`はURLエンコードにおける半角スペースを意味する。
ここで、ORを用いるのは、これらのAccessionのうちどれか一つでも合致するものを全てダウンロードする、という意味である。ANDを使ってしまうとAccessionにACC1, ACC2, ACC3の全てを持つ配列をダウンロードするという意味になってしまう。
なお、実際のスクリプトにおいてはcurlでエラーが発生した場合に再実行をするように--retryオプションが利用されている。

このように、ORで複数のAccessionを指定することが可能だが、その上限は100個までである。そのため、スクリプトではあらかじめ`id_list.txt`を100行ごとにサブファイルに分割した上で、サブファイルごとに全てのEntryIDをORで連結してからcurlに渡すように設計してある。

### 備考
本スクリプトの作成にはChatGPT(GPT-5)が活用された。
