__author__ = 'William R. George'


from functools import partial
# from matplotlib import pyplot as plt
import multiprocessing
from pprint import pprint
import statistics
from time import time
from timeit import timeit
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


class Bettor(object):
    title = 'Simple Bettor'
    color = 'k'
    members = 0
    dead = 0
    net_worth_list = []

    def __init__(self, initial_funds, initial_wager, roll_function=None, **kwargs):
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
            winnings = wager * 30
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

    def wager(self):
        wager = round_to_5(super().wager())
        return min(max(5, wager), 50)


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


def roll_craps():
    return random.randint(1, 6), random.randint(1, 6)

def roll_against_midnight():
    d1, d2 = roll_craps()
    return d1 + d2 == 12


def play(initial_funds, initial_wager, wager_count, bettor_class, **kwargs):
    player = bettor_class(initial_funds, initial_wager, **kwargs)

    rolls = ((wager_number, roll_against_midnight()) for wager_number in range(wager_count))
    for wager_number, roll in rolls:
            _ = player.play(wager_number, roll)

    return player


def mp_play(lose_multiple):
    lose_multiple = round(random.uniform(1, 15), 1)
    args = [initial_funds, initial_wager, wager_count, bettor_class]
    kwargs = {'lose_multiple': lose_multiple}
    return [play(*args, **kwargs) for _ in range(player_sample_size)]


def calc_stats(player_group, max_death_rate=100):
    stats = {}
    player = player_group[0]
    stats['class_name'] = player.__class__.__name__
    stats['lose_multiple'] = player.lose_multiple

    stats['members'] = 0
    stats['dead'] = 0

    net_worth_list = []
    non_bust_nw_list = []
    profit_nw_list = []

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

    stats['death_rate'] = stats['dead'] / stats['members'] * 100.0
    stats['avg_nw'] = statistics.mean(net_worth_list) if net_worth_list else 0
    stats['avg_nb_nw'] = statistics.mean(non_bust_nw_list) if non_bust_nw_list else 0

    stats['profit_rate'] = len(profit_nw_list) / stats['members'] * 100
    stats['avg_p_nw'] = statistics.mean(profit_nw_list) if profit_nw_list else 0


    return stats


def print_stats(stats):
    args = stats['class_name'], stats['lose_multiple']
    print('Stats for {}({:.4f}):'.format(*args))

    args = stats['death_rate'], 100 - stats['death_rate']
    print('  Death Rate: {:.2f}%\n  Survival Rate: {:.2f}%'.format(*args))

    args = stats['avg_nw'], stats['avg_nb_nw']
    print('  Avg Net   : ${:.2f}\t Avg Survivor\'s Net: ${:.2f}'.format(*args))

    args = (stats['profit_rate'], stats['avg_p_nw'])
    print('  Profit Rate: {:.2f}%\t Avg Profiter\'s Net: ${:.2f}'.format(*args))


# def run_scenario(pool):
#     player_groups = []
#     player_groups.extend(pool.map(mp_play, range(int(sample_size))))


wager_count = 100
initial_wager = 10
initial_funds = 1000
player_sample_size = 500
scenario_sample_size = 1000
# sample_size = 10000
bettor_class = SimpleWorkingBettor


if __name__ == '__main__':

    pool = multiprocessing.Pool(processes=6)

    divisions = 10
    stats_list = []
    rt_start = time()
    for div in range(1, divisions+1):
        drt_start = time()
        player_groups = []
        player_groups.extend(pool.map(mp_play,
                                      range(int(scenario_sample_size/divisions))))
        drt_end = time()
        drt = drt_end - drt_start
        print("betting over for division {}/{} after {:.3f} seconds".format(div,
                                                                            divisions,
                                                                            drt))
        stats_list.extend([calc_stats(player_group, max_death_rate=50)
                           for player_group in player_groups])
        del player_groups
    rt_end = time()
    rt = rt_end - rt_start
    print('Total betting time: {:.3f} seconds'.format(rt))
    for stats in stats_list:
        if stats['death_rate'] <= 50 and stats['profit_rate'] >= 40:
            print_stats(stats)

    # for player_group in player_groups:
    #     for player in player_group:
    #             player.__class__.members += 1
    #             if player.net_worth <= 0:
    #                 player.__class__.dead += 1
    #             player.__class__.net_worth_list.append(player.net_worth)
    #             x, y = split_points(player.networth_points)
    #             plt.plot(x, y)



    # for bettor_class in bettor_classes:
    #     title, dead, members, net_worth_list = (bettor_class.title,
    #                                             bettor_class.dead,
    #                                             bettor_class.members,
    #                                             bettor_class.net_worth_list)
    #     title = '{}({})'.format(title, bettor_class.color)
    #     death_rate = dead / members * 100
    #     print("{} death rate: {}".format(title, death_rate))
    #     if death_rate < 100:
    #         non_bust_nw_list = [net_worth for net_worth in net_worth_list if net_worth > 0]
    #         profit_nw_list = [net_worth for net_worth in net_worth_list if net_worth > initial_funds]
    #
    #         nb_avg = statistics.mean(non_bust_nw_list)
    #         profit_avg = statistics.mean(profit_nw_list)
    #
    #         print("{} {} survivor's worth: {:.2f}".format(title, len(non_bust_nw_list), nb_avg))
    #         print("{} {} profiter's worth: {:.2f}".format(title, len(profit_nw_list), profit_avg))

    #living_players = [player for player in players if player.current_funds > 0]
    #print("Survival Rate: {:.2f}%".format(len(living_players) / len(players) * 100))
    pool.close()
    pool.join()
    try:
        plt.ylabel('Net Worth')
        plt.xlabel('Wager Count')
    except:
        pass
    # plt.show()
