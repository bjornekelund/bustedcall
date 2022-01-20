#import __main__
#import re
from datetime import datetime

class Spot():

    def __init__(self, spotter, call, frequency, date):

        self.origin = spotter

        self.qrg = float(frequency)

        self.dx = call

        self.time = datetime.strptime(date, '%Y-%m-%d %H:%M:%S')
