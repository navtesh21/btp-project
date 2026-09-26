#!/bin/sh
set -e
cd /d/btp/data/physiocgm
# subject -> figshare file id (raw archives only)
for pair in \
  "c1s02_raw.zip 51653204" "c1s03_raw.zip 51653708" "c1s04_raw.zip 51655547" \
  "c1s05_raw.zip 51655562" "c2s01_raw.zip 51655571" "c2s02_raw.zip 51655574" \
  "c2s03_raw.zip 51655595" "c2s04_raw.zip 51655601" "c2s05_raw.zip 51655613"; do
  name=$(echo "$pair" | cut -d' ' -f1)
  fid=$(echo "$pair" | cut -d' ' -f2)
  if [ -f "$name" ]; then echo "skip $name"; continue; fi
  echo "downloading $name ..."
  curl -L -s -o "$name.part" "https://ndownloader.figshare.com/files/$fid"
  mv "$name.part" "$name"
  echo "done $name ($(du -h "$name" | cut -f1))"
done
echo "ALL RAW SUBJECTS DOWNLOADED"
