import random

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


def bpf_midnight_craps_game(**kwargs):
    initial_wager = kwargs['initial_wager']
    initial_funds = kwargs['initial_funds']
    kwargs['current_funds'] = initial_funds
    kwargs['current_wager'] = initial_wager
    kwargs['last_winnings'] = kwargs['last_wager'] = 0
    kwargs['net_worth_points'] = []

    rounds_per_game = kwargs['rounds_per_game']
    g_rounds = range(1, rounds_per_game + 1)

    for round_number in g_rounds:
        kwargs['current_round'] = round_number
        kwargs = bpf_midnight_craps_round(**kwargs)

    return kwargs


def bpf_midnight_craps_round(**kwargs):
    current_funds = kwargs['current_funds']
    if current_funds <= 0:
        return kwargs
    current_wager = kwargs['current_wager']
    last_wager = kwargs['last_wager']
    last_winnings = kwargs['last_winnings']
    round_number = kwargs['current_round']
    odds = 30

    # place bet
    progression_type = kwargs['progression_type']  #'unit', 'ratio', None
    progression_amt = kwargs['progression_amt']  #amount to add or multiply
    progression_interval = kwargs['progression_interval']  # number of losses
    if progression_amt and not round_number % progression_interval:
        if progression_type == 'unit':
            if not round_number % progression_interval:
                current_wager = last_wager + progression_amt
        elif progression_type == 'ratio':
            if not round_number % progression_interval:
                current_wager = last_wager * progression_amt
    current_wager = max(0, current_wager)

    current_funds -= current_wager

    # roll dice
    dice = random.randint(1, 6), random.randint(1, 6)
    if sum(dice) == 12:
        winnings = current_wager * odds
    else:
        winnings = 0

    current_funds += winnings

    kwargs['last_wager'] = current_wager
    kwargs['last_winnings'] = winnings

    kwargs['current_funds'] = current_funds
    kwargs['net_worth_points'].append((round_number, current_funds))
    kwargs['net_worth'] = current_funds
    return kwargs


def bpf_mg_midnight_craps_game(**kwargs):
    initial_wager = kwargs['initial_wager']
    initial_funds = kwargs['initial_funds']
    kwargs['current_funds'] = initial_funds
    kwargs['current_wager'] = initial_wager
    kwargs['last_winnings'] = kwargs['last_wager'] = 0
    kwargs['net_worth_points'] = []

    rounds_per_game = kwargs['rounds_per_game']
    g_rounds = range(1, rounds_per_game + 1)

    for round_number in g_rounds:
        kwargs['current_round'] = round_number
        kwargs = bpf_mg_midnight_craps_round(**kwargs)

    return kwargs


def bpf_mg_midnight_craps_round(**kwargs):
    from pprint import pprint
    current_funds = kwargs['current_funds']
    if current_funds <= 0:
        return kwargs
    current_wager = kwargs['current_wager']
    last_wager = kwargs['last_wager']
    last_winnings = kwargs['last_winnings']
    round_number = kwargs['current_round']
    odds = 30

    # place bet
    progression_type = kwargs['progression_type']  #'unit', 'ratio', None
    progression_amt = kwargs['progression_amt']  #amount to add or multiply
    progression_interval = kwargs['progression_interval']  # number of losses
    if progression_amt and not round_number % progression_interval and not last_winnings:
        if progression_type == 'unit':
            if not round_number % progression_interval:
                current_wager = last_wager + progression_amt
        elif progression_type == 'ratio':
            if not round_number % progression_interval:
                current_wager = last_wager * progression_amt
    current_wager = max(0, current_wager)

    current_funds -= current_wager

    # roll dice
    dice = random.randint(1, 6), random.randint(1, 6)
    if sum(dice) == 12:
        winnings = current_wager * odds
    else:
        winnings = 0

    current_funds += winnings

    kwargs['last_wager'] = current_wager
    kwargs['last_winnings'] = winnings

    kwargs['current_funds'] = current_funds
    kwargs['net_worth_points'].append((round_number, current_funds))
    kwargs['net_worth'] = current_funds
    return kwargs


def bpf_roulette_thirds_game(**kwargs):
    initial_wager = kwargs['initial_wager']
    initial_funds = kwargs['initial_funds']
    return