#!/usr/bin/env bash
# 使い方:
#   bash get_uniprot_fasta.sh id_list.txt output.fasta

IN="${1:-id_list.txt}"
OUT="${2:-uniprot.fasta}"
CHUNK=100   # 一度に取得するID数

# --- 入力確認 ---
if [[ ! -s "$IN" ]]; then
  echo "ERROR: 入力ファイルが見つからないか空です: $IN" >&2
  exit 1
fi

# --- 一時ファイルを作成 ---
TMP_PART_PREFIX="tmp_ids_part_"
TMP_OUT="tmp_all_downloaded.fasta"

# --- 分割 ---
split -l "$CHUNK" -d "$IN" "$TMP_PART_PREFIX"

# --- 各チャンクを順に取得 ---
for f in ${TMP_PART_PREFIX}*; do
  cnt=$(wc -l < "$f")
  # 各行を 'accession:ID' にして、'%20OR%20' で連結（URLエンコード済みの OR）
  query=$(tr -d '\r' < "$f" | awk 'NF{printf "accession:%s%%20OR%%20", $1}' | sed 's/%20OR%20$//')

  echo "Downloading ${cnt} IDs from $f ..."
  curl -sS --retry 6 --retry-delay 5 \
    "https://rest.uniprot.org/uniprotkb/stream?format=fasta&query=(${query})" \
    >> "$TMP_OUT"
  sleep 2
done

# --- 出力 ---
mv "$TMP_OUT" "$OUT"
echo "DONE: $OUT  (sequences: $(grep -c '^>' "$OUT"))"

# --- 一時ファイル削除 ---
rm -f ${TMP_PART_PREFIX}*
