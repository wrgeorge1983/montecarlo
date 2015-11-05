__author__ = 'William R. George'

import random

def iter_render(iterator):
    while True:
        try:
            iterator.__next__()
        except StopIteration:
            return


def round_to_5(number):
    lower5 = number // 5
    higher5 = lower5 + 5
    ldiff = number - lower5
    hdiff = higher5 - number
    return lower5 if ldiff < hdiff else higher5


def split_points(points):
    xList = []
    yList = []
    for x, y in points:
        xList.append(x)
        yList.append(y)
    return xList, yList


def roll_dice():
    roll = random.randint(1, 100)
    if 50 < roll < 100:
        return True
    return False


class Bettor(object):
    title = 'Simple Bettor'
    color = 'k'
    members = 0
    dead = 0
    net_worth_list = []

    def __init__(self, initial_funds, initial_wager, game, roll_function=None, **kwargs):
        self.current_funds = self.initial_funds = initial_funds
        self.bank = 0
        self.last_wager = self.initial_wager = initial_wager
        self.roll_function = roll_function
        self.fund_points = [] # list of two-tuples for x,y coordinates
        self.wager_points = []
        self.networth_points = []
        self.last_winnings = True
        self.__class__.members += 1
        self.game = game()
        self.verbose = False

    @property
    def net_worth(self):
        return self.bank + self.current_funds

    def determine_wager(self):
        return min(self.initial_wager, self.current_funds)

    def play(self, wager_number, roll=None):  #:bool=None):
        if self.current_funds <= 0:
            return 0

        # if roll is None:
        #     roll = self.roll_function() # should return bool

        wager = self.determine_wager()
        self.current_funds -= wager
        self.game.wager(wager, 17)
        self.current_funds -= wager
        self.game.wager(wager, 24)

        winnings, roll = self.game.play(roll)
        self.current_funds += winnings

        if self.net_worth <= 0:
            self.__class__.dead += 1

        self.fund_points.append((wager_number, self.current_funds))
        self.networth_points.append((wager_number, self.net_worth))
        self.wager_points.append((wager_number, wager))
        self.last_winnings = winnings
        self.last_wager = wager
        if self.verbose:
            print("NW:  {:.2f}\tFunds:  {:.2f}\twagered:  {:.2f}\trolled:  {}\twon:  {:.2f}".format(self.net_worth,
                                                                                                    self.current_funds,
                                                                                                    wager,
                                                                                                    roll, winnings))

        return self.current_funds, roll # for easy plotting


class BankingBettor(Bettor):
    """
    threshold_multiplier = 1.2 # start banking when we're at
    # `threshold_multiplier * initial_funds`
    banking_rate = .02 # how much to bank when we bank
    """

    # define these here so we can use them in random.choice later!
    threshold_targets = ['current_funds', 'net_worth']
    banking_targets = ['current_funds', 'net_worth',
                       'current_funds_gains', 'net_worth_gains',
                       'threshold_target_gains', 'threshold_target_over_threshold']

    def __init__(self, *args,
                 threshold_multiplier=1.2, threshold_target='current_funds',
                 banking_rate=0.2, banking_target='current_funds',
                 **kwargs):

        self.threshold_multiplier = threshold_multiplier
        self.threshold_target = threshold_target
        self.banking_rate = banking_rate
        self.banking_target = banking_target
        super().__init__(*args, **kwargs)

    def play(self, wager_number, roll=None):  #:bool=None):
        super().play(wager_number, roll)
        threshold = self.initial_funds * self.threshold_multiplier

        tt = self.threshold_target
        if tt == 'current_funds':
            threshold_target = self.current_funds
        elif tt == 'net_worth':
            threshold_target = self.net_worth
        else:
            raise ValueError('threshold_target is nonsense: {}'.format(tt))

        bt = self.banking_target
        if bt == 'current_funds':
            banking_target = self.current_funds
        elif bt == 'net_worth':
            banking_target = self.net_worth
        elif bt == 'current_funds_gains':
            banking_target = self.current_funds - self.initial_funds
        elif bt == 'net_worth_gains':
            banking_target = self.net_worth - self.initial_funds
        elif bt == 'threshold_target_gains':
            banking_target = threshold_target - self.initial_funds
        elif bt == 'threshold_target_over_threshold':
            banking_target = threshold_target - threshold
        else:
            raise ValueError('banking_target is nonsense: {}'.format(bt))

        if threshold_target > threshold:
            deposit = banking_target * self.banking_rate
            self.current_funds -= deposit
            self.bank += deposit
        # since we're assumed dead in Bettor.play() we plot ourselves here if
        # we have a positive networth but no current_funds
        if (self.current_funds <= 0) and (self.net_worth > 0):
            self.networth_points.append((wager_number, self.net_worth))


def n_func(**kwargs):
    return None

bank_schemes = {
}

games = {
    'bpf_midnight_craps': bpf_midnight_craps_game,
    'bpf_roulette_thirds': bpf_roulette_thirds_game,
}

def basic_player_func(**kwargs):
    history = kwargs.copy()
    kwargs['history'] = history
    game = games[kwargs['game']]
    game_sample_size = kwargs['game_sample_size']  # games to play
    kwargs['player_group'] = []
    for game in range(games):
        p_kwargs = kwargs.copy()
        kwargs['player_group'].append(bpf_midnight_craps_round(**p_kwargs))
    return kwargs


def bpf_midnight_craps_game(**kwargs):
    history = kwargs['history']
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
    round_number = kwargs['round_number']
    odds = 30

    # place bet
    progression_type = kwargs['progression_type']  #'unit', 'ratio', None
    progression_amt = kwargs['progression_amt']  #amount to add or multiply
    progression_interval = kwargs['progression_interval']  # number of losses
    if not round_number % progression_interval and progression_amt:
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
    return kwargs

def bpf_roulette_thirds_game(**kwargs):
    initial_wager = kwargs['initial_wager']
    initial_funds = kwargs['initial_funds']
    return

