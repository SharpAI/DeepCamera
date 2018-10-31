# -*- coding: UTF-8 -*-
import time


class Timer:
    def __init__(self, func=time.time):
        # self.elapsed = 0.0
        self._func = func
        self._start = None

    def restart(self):
        self.stime = self._func()

    def elapsed(self):
        return self._func() - self.stime

