__author__ = 'William R. George'

from random import randint, uniform


class Game(object):
    def __init__(self):
        self.clear()

    def clear(self):
        raise NotImplementedError


class MidnightCraps(Game):
    """
    Simulates rolls against 6-6 (midnight) in craps
    """

    def clear(self):
        self._wager = {12:0}

    def wager(self, value, roll=12):
        self._wager[roll] = value

    def roll(self):
        return randint(1, 6) + randint(1,6)

    def play(self, roll=None):
        winnings = 0
        if roll is None:
            roll = self.roll()

        if roll == 12:
            winnings = (self._wager[12] * 30) + 1
        self.clear()
        return winnings, roll


class SimpleRoulette(Game):
    """
    Simple roulette simulation
    """
    def clear(self):
        self._wager = {key: 0 for key in range(-1, 37)}

    def wager(self, value, spin):
        self._wager[spin] = value

    def spin(self):
        return randint(-1, 36)

    def play(self, spin=None):
        winning = 0
        if spin is None:
            spin = self.spin()

        winnings = (self._wager[spin] * 37)
        self.clear()
        return winnings, spin

