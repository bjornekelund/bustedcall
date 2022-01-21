#!/bin/bash

if [ "$1" != "" ]; then
  FILE=$1
else
  FILE=20211123
fi

echo Fetching data
./getdata.bash $FILE

echo Starting analysis

./bustedcall.py $FILE.csv > result.txt

echo Done. Result is in result.txt

exit
