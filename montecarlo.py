__author__ = 'William R. George'


from functools import partial
from matplotlib import pyplot as plt
import multiprocessing
from pprint import pprint
import statistics
from timeit import timeit
import random


def split_points(points):
    xList = []
    yList = []
    for x, y in points:
        xList.append(x)
        yList.append(y)
    return xList, yList


class Bettor(object):
    title = 'Simple Bettor'
    color = 'k'
    members = 0
    dead = 0
    net_worth_list = []

    def __init__(self, initial_funds, initial_wager, roll_function=None):
        self.current_funds = self.initial_funds = initial_funds
        self.bank = 0
        self.last_wager = self.initial_wager = initial_wager
        self.roll_function = roll_function
        self.fund_points = [] # list of two-tuples for x,y coordinates
        self.wager_points = []
        self.networth_points = []
        self.last_roll = True
        self.__class__.members += 1

    @property
    def net_worth(self):
        return self.bank + self.current_funds

    def wager(self):
        return min(self.initial_wager, self.current_funds)

    def play(self, wager_number, roll):  #:bool=None):
        if self.current_funds <= 0:
            return 0

        # if roll is None:
        #     roll = self.roll_function() # should return bool

        wager = self.wager()
        if roll:
            winnings = wager * 1.1
        else:
            winnings = wager * -1
        self.current_funds += winnings

        if self.net_worth <= 0:
            self.__class__.dead += 1

        self.fund_points.append((wager_number, self.current_funds))
        self.networth_points.append((wager_number, self.net_worth))
        self.wager_points.append((wager_number, wager))
        self.last_roll = roll
        self.last_wager = wager
        return self.current_funds, roll # for easy plotting


class BankingBettor(Bettor):
    threshold_multiplier = 1.2 # start banking when we're at
    # `threshold_multiplier * initial_funds`
    banking_rate = .02 # how much to bank when we bank

    def play(self, wager_number, roll):  #:bool=None):
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


class SimpleMartingaleBettor(Bettor):
    title = 'Simple Doubler Bettor'
    color = 'r'
    members = 0
    dead = 0
    net_worth_list = []

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.win_multiple = 1
        self.lose_multiple = 2

    def wager(self):
        if not self.last_roll:
            wager = self.last_wager * self.lose_multiple
        else:
            wager = self.initial_wager
        return min(wager, self.current_funds)


class ComplexMartingaleBettor(SimpleMartingaleBettor):
    title = 'Complex Doubler Bettor'
    color = 'c'
    members = 0
    dead = 0
    net_worth_list = []

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.win_multiple = self.initial_wager / self.initial_funds
        self.winstreak = 0

    def wager(self):
        if not self.last_roll:
            self.winstreak = 0
            wager = super().wager()
        else:
            self.winstreak += 1
            wager = self.current_funds * self.win_multiple

        return min(wager, self.current_funds)


class ComplexBankingMartinBettor(BankingBettor, ComplexMartingaleBettor):
    title = 'Complex Banking Martin Bettor'
    color = 'g'
    members = 0
    dead = 0
    net_worth_list = []


class SimpleWorkingBettor(SimpleMartingaleBettor):
    title = 'Simple Working Bettor'
    color = 'b'
    members = 0
    dead = 0
    net_worth_list = []

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        try:
            self.lose_multiple = kwargs['lose_multiple']
        except KeyError:
            self.lose_multiple = 2


class SimpleBankingWorkingBettor(BankingBettor, SimpleWorkingBettor):
    title = 'Simple Banking Working Bettor'
    color = 'm'
    members = 0
    dead = 0
    net_worth_list = []


class ComplexWorkingBettor(SimpleWorkingBettor, ComplexMartingaleBettor):
    title = 'Complex Working Bettor'
    color = 'm'
    members = 0
    dead = 0
    net_worth_list = []

class ComplexBankingWorkingBettor(BankingBettor, ComplexWorkingBettor):
    title = 'Complex Banking Working Bettor'
    color = 'y'
    members = 0
    dead = 0
    net_worth_list = []

def roll_dice():
    roll = random.randint(1, 100)
    if 50 < roll < 100:
        return True
    return False


def play(initial_funds, initial_wager, wager_count, bettor_class, **kwargs):
    player = bettor_class(initial_funds, initial_wager, **kwargs)

    rolls = ((wager_number, roll_dice()) for wager_number in range(wager_count))
    for wager_number, roll in rolls:
            _ = player.play(wager_number, roll)

    return player


def mp_play(lose_multiple):
    return play(initial_funds, initial_wager, wager_count, bettor_class, lose_multiple=lose_multiple)


def calc_stats(player_group):
    stats = {}
    player = player_group[0]
    stats['lose_multiple'] = player.lose_multiple

    stats['members'] = 0
    stats['dead'] = 0

    stats['net_worth_list'] = net_worth_list = []
    stats['non_bust_nw_list'] = non_bust_nw_list = []
    stats['profit_nw_list'] = profit_nw_list = []

    for player in player_group:
        stats['members'] += 1
        net_worth = player.net_worth
        if net_worth <= 0:
            stats['dead'] += 1
        else:
            non_bust_nw_list.append(net_worth)
            if net_worth > initial_funds:
                profit_nw_list.append(net_worth)

        net_worth_list.append(player.net_worth)
    return stats



def run_scenario(pool):
    player_groups = []
    player_groups.extend(pool.map(mp_play, range(int(sample_size))))


wager_count = 1500
initial_wager = 100
initial_funds = 10000
player_sample_size = 1000
scenario_sample_size = 10
sample_size = 10000

if __name__ == '__main__':

    player_groups = []
    pool = multiprocessing.Pool(processes=8)
    player_groups.extend(pool.map(mp_play, range(int(sample_size / 2))))
    print("betting over")

    for player_group in player_groups:
        for player in player_group:
                player.__class__.members += 1
                if player.net_worth <= 0:
                    player.__class__.dead += 1
                player.__class__.net_worth_list.append(player.net_worth)
                x, y = split_points(player.networth_points)
                plt.plot(x, y, player.color)


    for bettor_class in bettor_classes:
        title, dead, members, net_worth_list = (bettor_class.title,
                                                bettor_class.dead,
                                                bettor_class.members,
                                                bettor_class.net_worth_list)
        title = '{}({})'.format(title, bettor_class.color)
        death_rate = dead / members * 100
        print("{} death rate: {}".format(title, death_rate))
        if death_rate < 100:
            non_bust_nw_list = [net_worth for net_worth in net_worth_list if net_worth > 0]
            profit_nw_list = [net_worth for net_worth in net_worth_list if net_worth > initial_funds]

            nb_avg = statistics.mean(non_bust_nw_list)
            profit_avg = statistics.mean(profit_nw_list)

            print("{} {} survivor's worth: {:.2f}".format(title, len(non_bust_nw_list), nb_avg))
            print("{} {} profiter's worth: {:.2f}".format(title, len(profit_nw_list), profit_avg))

    #living_players = [player for player in players if player.current_funds > 0]
    #print("Survival Rate: {:.2f}%".format(len(living_players) / len(players) * 100))
    plt.ylabel('Net Worth')
    plt.xlabel('Wager Count')
    plt.show()
    pool.close()
    pool.join()

