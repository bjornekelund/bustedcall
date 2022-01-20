#!/bin/bash
# ./bustedcall.py -m 2 20211127.csv -a > max2ascii.txt
# ./bustedcall.py -m 3 20211127.csv -a > max3ascii.txt
# ./bustedcall.py -m 5 20211127.csv > max5morse.txt
# ./bustedcall.py -m 6 20211127.csv > max5morse.txt

./bustedcall.py -m 2 20211127.csv -a -p > max2ascii.txt
./bustedcall.py -m 3 20211127.csv -a -p > max3ascii.txt
./bustedcall.py -m 5 20211127.csv -p > max5morse.txt
./bustedcall.py -m 6 20211127.csv -p > max5morse.txt

exit
