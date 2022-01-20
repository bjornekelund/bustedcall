#!/bin/bash
DATES="20211123 20211127 20211128 20220111"
for date in $DATES; do
  ZIP="$date.gz"
  CSV="$date.csv"
  rm -f $CSV $ZIP
  echo "Downloading" $ZIP
  wget --quiet --no-hsts http://reversebeacon.net/raw_data/dl.php?f=$date -O $ZIP
  echo "Unzipping" $CSV
  gunzip $ZIP
  mv $date $CSV
  echo "Done"
done
echo "Downloading MASTER.SCP"
rm -f MASTER.SCP
wget --quiet --no-hsts http://www.supercheckpartial.com/MASTER.SCP
echo "Done"
exit
