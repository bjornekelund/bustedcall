#!/bin/bash
#set -x

if [ "$1" != "" ]; then
  DATES=$1
else
  DATES="20211123 20211127 20211128 20220111"
fi

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

