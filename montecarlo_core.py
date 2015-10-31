__author__ = 'William R. George'



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
        self.game = game
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
            print("NW:  {:.2f}\tFunds:  {:.2f}\twagered:  {:.2f}\trolled:  {}\twon:  {:.2f}".format(wager,
                                                                                                    roll, winnings))

        return self.current_funds, roll # for easy plotting


class BankingBettor(Bettor):
    threshold_multiplier = 1.2 # start banking when we're at
    # `threshold_multiplier * initial_funds`
    banking_rate = .02 # how much to bank when we bank

    def play(self, wager_number, roll=None):  #:bool=None):
        super().play(wager_number, roll)
        threshold = self.initial_funds * self.threshold_multiplier
        if self.current_funds >= threshold:
            deposit = (self.current_funds - threshold) * self.banking_rate
            self.current_funds -= deposit
            self.bank += deposit
        # since we're assumed dead in Bettor.play() we plot ourselves here if
        # we have a positive networth but no current_funds
        if (self.current_funds <= 0) and (self.net_worth > 0):
            self.networth_points.append((wager_number, self.net_worth))



