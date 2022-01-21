#!/bin/bash
echo Fetching data

./getdata.bash

echo Starting analysis

./bustedcall.py 20211127.csv > result.txt

echo Done. Result is in result.txt

exit
