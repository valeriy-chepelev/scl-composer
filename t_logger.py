from time import monotonic as clock
from functools import reduce

def secondsToStr(t):
    return "%d:%02d:%02d.%03d" % \
        reduce(lambda ll,b : divmod(ll[0],b) + ll[1:],
            [(t*1000,),1000,60,60])

class T_logger():
    def __init__(self):
        self.story = dict()
        self.start = clock()

    def log(self, event = ''):
        end = clock()
        self.story[event] = secondsToStr(end - self.start)
        self.start = clock()
        
