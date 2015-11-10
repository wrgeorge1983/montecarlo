__author__ = 'William R. George'


from functools import partial
try:
    from matplotlib import pyplot as plt
except ImportError:
    pass
import multiprocessing
from pprint import pprint
try:
    from numpy import mean
except:
    from statistics import mean

from time import time
from timeit import timeit
try:
    from numpy.random import randint, uniform
except:
    from random import randint, uniform

import games
from martingale_bettors import SimpleWorkingBettor
from montecarlo_core import basic_player_func


def roll_craps():
    return randint(1, 6), randint(1, 6)


def roll_against_midnight():
    d1, d2 = roll_craps()
    return d1 + d2 == 12


def play(initial_funds, initial_wager, wager_count, bettor_class, game, **kwargs):
    player = bettor_class(initial_funds, initial_wager, game, **kwargs)

    player.wager_count = wager_count  # just for later inspection

    for wager_number in range(wager_count):
            _ = player.play(wager_number)

    return player


def mp_play(lose_multiple):
    if lose_multiple is None:
        lose_multiple = round(uniform(1.1, 5.0), 2)
    args = [initial_funds, initial_wager, wager_count, bettor_class, game]
    kwargs = {'lose_multiple': lose_multiple}
    return [play(*args, **kwargs) for _ in range(player_sample_size)]


def calc_stats(player_group, max_death_rate=100):
    stats = {}
    player = player_group[0]
    # stats['class_name'] = player.__class__.__name__
    stats['class_name'] = player['class_name']
    stats['wager_count'] = player['wager_count']
    stats['initial_funds'] = player['initial_funds']
    stats['initial_wager'] = player['initial_wager']

    stats['lose_multiple'] = player.get('lose_multiple', 1)

    stats['members'] = 0
    stats['dead'] = 0

    net_worth_list = []
    non_bust_nw_list = []
    profit_nw_list = []

    for player in player_group:
        stats['members'] += 1
        net_worth = player['net_worth']
        if net_worth <= 0:
            stats['dead'] += 1
        else:
            non_bust_nw_list.append(net_worth)
            if net_worth > initial_funds:
                profit_nw_list.append(net_worth)
        try:
            plt.plot(*split_points(player['networth_points']))
        except NameError:
            pass
        net_worth_list.append(net_worth)

    stats['death_rate'] = stats['dead'] / stats['members'] * 100.0
    stats['avg_nw'] = mean(net_worth_list) if net_worth_list else 0
    stats['avg_nb_nw'] = mean(non_bust_nw_list) if non_bust_nw_list else 0

    stats['profit_rate'] = len(profit_nw_list) / stats['members'] * 100
    stats['avg_p_nw'] = mean(profit_nw_list) if profit_nw_list else 0

    return stats

def calc_stats_bpf(**kwargs):
    stats = kwargs


    net_worth_list = []
    non_bust_nw_list = []
    profit_nw_list = []
    stats['members'] = stats['dead'] = 0

    for player in stats['player_group']:
        stats['members'] += 1
        net_worth = player['net_worth']
        if net_worth <= 0:
            stats['dead'] += 1
        else:
            non_bust_nw_list.append(net_worth)
            if net_worth > initial_funds:
                profit_nw_list.append(net_worth)
        del player['net_worth_points']
        net_worth_list.append(net_worth)

    stats['death_rate'] = stats['dead'] / stats['members'] * 100.0
    stats['avg_nw'] = mean(net_worth_list) if net_worth_list else 0
    stats['avg_nb_nw'] = mean(non_bust_nw_list) if non_bust_nw_list else 0

    stats['profit_rate'] = len(profit_nw_list) / stats['members'] * 100
    stats['avg_p_nw'] = mean(profit_nw_list) if profit_nw_list else 0

    del stats['player_group']

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


wager_count = 50
initial_wager = 1
initial_funds = 2000
player_sample_size = 10000
scenario_lbound = 1.5
scenario_ubound = 2.5
scenario_increment = .1
scenario_round_precision = 1
scenarios = [round(scenario_lbound + (scenario_increment * increment), scenario_round_precision)
             for increment in range(int(round((scenario_ubound - scenario_lbound)/scenario_increment, scenario_round_precision)))]
scenario_sample_size = 500
bettor_class = SimpleWorkingBettor
game = games.SimpleRoulette()

if __name__ == '__main__':

    pool = multiprocessing.Pool(processes=6)

    divisions = 10
    div_increment = len(scenarios) // divisions
    stats_list = []
    rt_start = time()
    for div in range(1, divisions+1):
        drt_start = time()
        player_groups = []

        div_lbound = (div - 1) * div_increment
        div_ubound = div_lbound + div_increment
        div_scenarios = scenarios[div_lbound:div_ubound]
        player_groups.extend(pool.map(mp_play,
                                      div_scenarios))
        drt_end = time()
        drt = drt_end - drt_start
        print("betting over for division {}/{} after {:.3f} seconds".format(div,
                                                                            divisions,
                                                                            drt))
        stats_list.extend([calc_stats(player_group, max_death_rate=100)
                           for player_group in player_groups])
        del player_groups
    rt_end = time()
    rt = rt_end - rt_start
    print('Total betting time: {:.3f} seconds'.format(rt))
    for stats in stats_list:
        if stats['death_rate'] < 50 and stats['profit_rate'] >= 25:
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
    #         nb_avg = mean(non_bust_nw_list)
    #         profit_avg = mean(profit_nw_list)
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
        plt.show()
    except NameError:
        pass
    # plt.show()
