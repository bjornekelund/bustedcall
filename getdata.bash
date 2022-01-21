#!/bin/bash
#set -x
#DATES="20211123 20211127 20211128 20220111"
DATES="20211123 20211127"
for date in $DATES; do
  ZIP="$date.gz"
  CSV="$date.csv"
  rm -f $CSV $ZIP
  wget --quiet --no-hsts http://reversebeacon.net/raw_data/dl.php?f=$date -O $ZIP
  gunzip < $ZIP > $CSV
  echo "Downloaded" $CSV
done
rm -f MASTER.SCP *.gz
wget --quiet --no-hsts http://www.supercheckpartial.com/MASTER.SCP
echo "Downloaded MASTER.SCP"
exit

