#!/usr/bin/python3
from Levenshtein import distance
import csv
from datetime import datetime
import sys

#FILE="20211123.csv"
# FILE="test.csv"
FILE="small.csv"
MASTER="MASTER.SCP"

USEMORSE = True
MORSEMAXDISTS = [3, 4, 5]
ASCIIMAXDISTS = [1, 2, 3]
CT1BOHMAXDIST = [10]

WINDOW = 15 # RBN bust buffer size in seconds
FIFO1 = [] # RBN buffer

FREQMARGIN = 0.1 # Maximum acceptable offset to be considered the same frequency

SPOTS = [] # Spots array
VALIDATEDCALLS = [] # Valid callsigns array

MORSE = {
    "A" : ".-",
    "B" : "-...",
    "C" : "-.-.",
    "D" : "-..",
    "E" : ".",
    "F" : "..-.",
    "G" : "--.",
    "H" : "....",
    "I" : "..",
    "J" : ".---",
    "K" : "-.-",
    "L" : ".-..",
    "M" : "--",
    "N" : "-.",
    "O" : "---",
    "P" : ".--.",
    "Q" : "--.-" ,
    "R" : ".-." ,
    "S" : "...",
    "T" : "-",
    "U" : "..-",
    "V" : "...-",
    "W" : ".--",
    "X" : "-..-",
    "Y" : "-.--",
    "Z" : "--..",
    "0" : "-----",
    "1" : ".----",
    "2" : "..---",
    "3" : "...--",
    "4" : "....-",
    "5" : ".....",
    "6" : "-....",
    "7" : "--...",
    "8" : "---..",
    "9" : "----.",
    "/" : "-..-.",
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

def levenshtein(validspot, checkspot, freqmargin, metric):
    if abs(validspot.qrg - checkspot.qrg) <= freqmargin:
        if metric == "Absolute Morse":
            result = distance(validspot.morse, checkspot.morse)
        elif metric == "Relative Morse":
            mlen = len(validspot.morse) if len(validspot.morse) > len(checkspot.morse) else len(checkspot.morse)
            result = int(5.0 * distance(validspot.morse, checkspot.morse) / mlen + 0.5)
        elif metric == "Absolute ASCII":
            result = distance(validspot.dx, checkspot.dx)
        elif metric == "Relative ASCII":
            mlen = len(validspot.dx) if len(validspot.dx) > len(checkspot.dx) else len(checkspot.dx)
            result = int(10.0 * distance(validspot.dx, checkspot.dx) / mlen + 0.5)
        elif metric == "CT1BOH":
            # The CT1BOH metric is actually a "match" and not a "distance" but this is the mathematical equivalent 
            # when the maximum acceptable distance is 10
            mlen = len(validspot.dx) if len(validspot.dx) > len(checkspot.dx) else len(checkspot.dx)
            result = int(24.0 * distance(validspot.dx, checkspot.dx) / mlen)
        else:
            exit(1)

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
        self.valid = call in VALIDATEDCALLS
        self.exposed = "/" in call
        # if not self.valid:
            # print("Call %8s QRG %5.1f Morse \"%s\"" % (self.dx, self.qrg, self.morse))

if __name__ == "__main__":
    for i in range(1, len(sys.argv)):
        FILE = sys.argv[i]

    # Load the MASTER.SCP database in global array VALIDATEDCALLS

    call_count = 0
    with open(MASTER) as f:
        calls = f.read().splitlines()
        for call in calls:
            if not call.startswith("#"):
                # print(f'Added line "{call}"')
                VALIDATEDCALLS.append(call)
                call_count += 1
    f.close()
    # print(f'Loaded {call_count} validated calls.')

    sys.stderr.write(f'Loaded {call_count} validated calls\n')
    sys.stderr.flush()


    # Load all spots in global array SPOTS

    # Counters
    spot_count = -1
    valid_count = 0

    # Indices of the information elements in the CSV file
    # Set to invalid numbers so we crash if a field is missing
    ispotter = -1
    idx = -1
    idate = -1
    ifreq = -1
    imode = -1

    print("Reading file %s..." % FILE)
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
                # if len(row) >= idate and contestband(row[ifreq]) and row[imode] == 'CW':
                if len(row) >= idate and row[imode] == 'CW':
                    newspot = Spot(row[ispotter], row[idx], row[ifreq], row[idate])
                    if newspot.valid:
                        valid_count += 1
                    SPOTS.append(newspot)
                    spot_count += 1
                    if spot_count % 10000 == 0:
                        sys.stderr.write(f'Building spot database, spot #{spot_count}\n')
                        sys.stderr.flush()
    csv_file.close()

    print("Processed %d spots of which %d are of known good calls" % (spot_count, valid_count))

    # Now traverse the entire spot array and find busted calls
    # A busted spot is defined as
    #   Appearing after the spot of the correct call
    #   Appearing on roughly  the same frequency
    #   Having a distorted version of the correct call

    analysis_count = 1
    for showonlymax in (False, True): # Show all and only the worst
        for metric in ["Absolute Morse", "Absolute ASCII", "CT1BOH"]: # For both methods
            if "Morse" in metric:
                dists = MORSEMAXDISTS
            elif "ASCII" in metric:
                dists = ASCIIMAXDISTS
            elif "CT1BOH" in metric:
                dists = CT1BOHMAXDIST
            else:
                exit(1)

            for maxdist in dists: # For all studied max distances
                FIFO1 = []
                # Start analysis
                print("-------------------------------------")
                sys.stderr.write(f'Performing analysis {analysis_count} of {2 * (len(MORSEMAXDISTS) + len(ASCIIMAXDISTS) + 1)}\n')
                sys.stderr.flush()
                analysis_count += 1
                print("Starting analysis for %s-based metric with maximum distance of %d" % (metric, maxdist))
                if showonlymax:
                    print("Showing only maximum distance busts")
                count_bust = 0
                # For each spot in the daily archive
                for newspot in SPOTS:
                    FIFO1.append(newspot)
                    # Process all spots at the oldest end of the FIFO that about to expire
                    while (FIFO1[-1].time - FIFO1[0].time).total_seconds() > WINDOW:
                        # Pop oldest spot
                        spot = FIFO1.pop(0)
                        if spot.valid: # If it is a known callsign
                            for check in FIFO1[:-1]: # Scan for busted versions of the known call in the FIFO
                                if not check.exposed and not check.valid:
                                    # ctime = check.time.strftime("%H:%M:%S")
                                    # stime = spot.time.strftime("%H:%M:%S")
                                    # print("%s time %s, %s time %s" % (check.dx, ctime, spot.dx, stime))
                                    dist = levenshtein(spot, check, FREQMARGIN, metric)
                                    if (showonlymax and (dist == maxdist)) or (not showonlymax and (dist > 0 and dist <= maxdist)):
                                        check.exposed = True # Don't display a busted spot more than once
                                        fdelta = abs(check.qrg - spot.qrg)
                                        tdelta = (check.time - spot.time).total_seconds()
                                        count_bust += 1
                                        print("Busted spot %8s (%8s) with distance %d, %2.0fs after correct call and %.1f kHz off" % (check.dx, spot.dx, dist, tdelta, fdelta))
                if showonlymax:
                    print("A total of %d busted spots with an exact distance of %d for %s-Levenshtein method" % (count_bust, maxdist, metric))
                else:
                    print("A total of %d busted spots with distance of maximum %d for %s-Levenshtein method" % (count_bust, maxdist, metric))
                for spot in SPOTS:
                    spot.exposed = False
    exit(0)
