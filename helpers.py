#!/bin/python3

# from spot import Spot
import re
from datetime import datetime

def contestband(freq):
    bands = [(1800, 2000), (3500, 3800), (7000, 7300), (14000, 14350), (21000, 21450), (28000, 29700)]
    for (lower, upper) in bands:
        if freq >= lower and freq <= upper:
            return True
    return False

def modeisCW(line):
    if (re.match(".+ CW ", line)):
        return True
    else:
        return False

def isskimmer(line):
    if (re.match(".+[A-Z]\-#: ", line)):
        return True
    else:
        return False

def since(time):
    return round((datetime.utcnow() - time).total_seconds(), 0)
