#!/bin/python3

from Levenshtein import distance
import csv
from datetime import datetime

#FILE="20211123.csv"
#FILE="test.csv"
FILE="small.csv"
MASTER="MASTER.SCP"

WINDOW = 60 # RBN bust buffer size in seconds
FIFO1 = [] # RBN buffer

FREQMARGIN = 0.3 # Acceptable offset to be considered the same frequency

SPOTS = [] # Spots array
SCP = [] # Valid callsigns array

MORSE = {
    "A" : ".- ",
    "B" : "-... ",
    "C" : "-.-. ",
    "D" : "-.. ",
    "E" : ". ",
    "F" : "..-. ",
    "G" : "--. ",
    "H" : ".... ",
    "I" : ".. ",
    "J" : ".--- ",
    "K" : "-.- ",
    "L" : ".-.. ",
    "M" : "-- ",
    "N" : "-. ",
    "O" : "--- ",
    "P" : ".--. ",
    "Q" : "--.- ",
    "R" : ".-. ",
    "S" : "... ",
    "T" : "- ",
    "U" : "..- ",
    "V" : "...- ",
    "W" : ".-- ",
    "X" : "-..- ",
    "Y" : "-.-- ",
    "Z" : "--.. ",
    "0" : "----- ",
    "1" : ".---- ",
    "2" : "..--- ",
    "3" : "...-- ",
    "4" : "....- ",
    "5" : "..... ",
    "6" : "-.... ",
    "7" : "--... ",
    "8" : "---.. ",
    "9" : "----. ",
    "/" : "-..-. ",
}

def contestband(freqstring):
    bands = [(1800, 2000), (3500, 3800), (7000, 7300), (14000, 14350), (21000, 21450), (28000, 29700)]
    freq = float(freqstring)
    for (lower, upper) in bands:
        if freq >= lower and freq <= upper:
            return True
    return False

def morse(callsign):
    result = ""
    for char in callsign:
        result += MORSE[char]
    return result[0:-1] # Prune last space

def levenshtein(validspot, checkspot, freqmargin):
    if abs(validspot.qrg - checkspot.qrg) <= freqmargin:
        dist = distance(validspot.morse, checkspot.morse)
        # dist = distance(validspot.dx, checkspot.dx)
        result = dist
        # print(f'Reference {validspot.dx}@{validspot.qrg} and {checkspot.dx}@{checkspot.qrg} distance is {dist}')
    else:
        result = 99
    return result

class Spot():
    def __init__(self, spotter, call, frequency, date):
        self.origin = spotter
        self.qrg = float(frequency)
        self.dx = call
        self.time = datetime.strptime(date, '%Y-%m-%d %H:%M:%S')
        self.morse = morse(call)
        self.valid = call in SCP       
        self.exposed = False
        # print("Call %8s QRG %5.1f Morse \"%s\"" % (self.dx, self.qrg, self.morse))           
       
# Load the MASTER.SCP database in global array SCP

#calls = []
call_count = 0
with open(MASTER) as f:
    calls = f.read().splitlines()
    for call in calls:
        if not call.startswith("#"):
            # print(f'Added line "{call}"')
            SCP.append(call)
            call_count += 1          
f.close()
print(f'Processed {call_count} calls.')

# Load all spots in global array SPOTS

spot_count = -1
valid_count = 0
ispotter = 0
idx = 0
idate =0
ifreq = 0
imode = 0
with open(FILE) as csv_file:
    csv_reader = csv.reader(csv_file, delimiter=',')
    for row in csv_reader:
        if spot_count == -1:
            for i in range(0, len(row)):
                if row[i] == "callsign": 
                    ispotter = i
                if row[i] == "dx":
                    idx = i
                if row[i] == "date":
                    idate = i
                if row[i] == "freq":
                    ifreq = i
                if row[i] == "tx_mode":
                    imode = i
            # print(f'Spotter is {ispotter}, dx is {idx}, freq is {ifreq}, and date is {idate}')
            spot_count = 0
        else:
            if len(row) >= idate and contestband(row[ifreq]) and row[imode] == 'CW':
                newspot = Spot(row[ispotter], row[idx], row[ifreq], row[idate])
                if newspot.valid:
                    valid_count += 1
                SPOTS.append(newspot)
                spot_count += 1
                if spot_count % 10000 == 0:
                    print(f'Building spot array, spot #{spot_count}')
csv_file.close()
print(f'Processed {spot_count} spots of which {valid_count} validated.')
    
# Now traverse the entire spot array and find busted calls
# A busted call is roughly on the same frequency and has a small enough difference to a valid call within the time window

for newspot in SPOTS:
    FIFO1.append(newspot)
    # Process all spots at the oldest end of the FIFO that about to expire
    while (FIFO1[-1].time - FIFO1[0].time).total_seconds() > WINDOW:
        spot = FIFO1.pop(0)
        if spot.valid: # If it is a known callsign
            for check in FIFO1: # Check for "bad copies" in the FIFO
                if not check.valid and not check.exposed:
                    check.exposed = True # Don't display a bad spot more than once
                    tdelta = (check.time - spot.time).total_seconds()
                    fdelta = abs(check.qrg - spot.qrg)
                    dist = levenshtein(spot, check, FREQMARGIN)
                    if dist <= 5:
                        print("Busted spot %8s %.0f seconds apart and %.1f kHz apart (should be %s distance is %d)" % (check.dx, tdelta, fdelta, spot.dx, dist))
            