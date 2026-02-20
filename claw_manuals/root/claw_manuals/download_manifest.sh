#!/usr/bin/env bash
set -euo pipefail
BASE=/data/.openclaw/workspace/water_manuals_dataset
MANIFEST="$BASE/manifest.tsv"
LOG="$BASE/logs/download_log.txt"
FAIL="$BASE/logs/failed_urls.txt"

slug(){
  # lowercase, replace non-alnum with underscore, trim underscores
  echo "$1" | tr '[:upper:]' '[:lower:]' | sed -E 's/[^a-z0-9]+/_/g; s/^_+//; s/_+$//'
}

# Use a non-whitespace delimiter (FS) so empty fields are preserved.
DELIM=$'\034'
while IFS="$DELIM" read -r category org brand title model doc_type language pubdate url; do
  [[ -z "${category:-}" || "$category" == "#"* ]] && continue

  org_slug=$(slug "$org")
  brand_slug=$(slug "$brand")
  title_slug=$(slug "$title")
  model_slug=$(slug "$model")
  doc_slug=$(slug "$doc_type")

  # filename convention: {org}_{brand}_{model}_{doc}_{shorttitle}.pdf (omit empty parts)
  parts=("$org_slug")
  [[ -n "$brand_slug" ]] && parts+=("$brand_slug")
  [[ -n "$model_slug" ]] && parts+=("$model_slug")
  [[ -n "$doc_slug" ]] && parts+=("$doc_slug")
  parts+=("$title_slug")
  fname=$(IFS=_; echo "${parts[*]}").pdf

  outdir="$BASE/$category/$org_slug"
  mkdir -p "$outdir"
  outpath="$outdir/$fname"

  downloaded_now=0
  if [[ -s "$outpath" ]]; then
    echo "SKIP_EXISTS\t$outpath\t$url" >> "$LOG"
  else
    downloaded_now=1
    echo "DOWNLOAD\t$outpath\t$url" >> "$LOG"
    if ! curl -L --fail --silent --show-error --connect-timeout 20 --max-time 300 -o "$outpath" "$url"; then
      echo -e "FAIL\t$url\t$outpath" >> "$FAIL"
      rm -f "$outpath" || true
      continue
    fi
    # sanity check: begins with %PDF
    if ! head -c 4 "$outpath" | grep -q '%PDF'; then
      echo -e "NOTPDF\t$url\t$outpath" >> "$FAIL"
      rm -f "$outpath" || true
      continue
    fi
  fi

  # add/update index
  res=$(node "$BASE/indexer.mjs" add \
    --file_path "$outpath" \
    --category "$category" \
    --org "$org" \
    --brand "$brand" \
    --title "$title" \
    --model_or_series "$model" \
    --doc_type "$doc_type" \
    --language "$language" \
    --publication_date "$pubdate" \
    --primary_url "$url")

  status=$(echo "$res" | node -e 'const fs=require("fs");const s=fs.readFileSync(0,"utf8");process.stdout.write(JSON.parse(s).status||"")' 2>/dev/null || echo "")
  if [[ "$status" == "deduped" ]]; then
    # remove duplicate file only if we downloaded it in this run
    if [[ "$downloaded_now" == "1" ]]; then
      echo "DEDUP_REMOVE\t$outpath\t$url" >> "$LOG"
      rm -f "$outpath" || true
    else
      echo "DEDUP_KEEP_EXISTING\t$outpath\t$url" >> "$LOG"
    fi
  else
    echo "INDEXED\t$outpath\t$res" >> "$LOG"
  fi

done < <(awk -F'\t' 'BEGIN{OFS=sprintf("%c",28)} NF>0{print $1,$2,$3,$4,$5,$6,$7,$8,$9}' "$MANIFEST")

echo "Done. Index: $BASE/manual_index.json and .csv"