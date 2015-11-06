__author__ = 'William.George'

import json
from pprint import pprint
import time
import zmq

import games
import montecarlo
import martingale_bettors
import montecarlo_core
from zmqVent import snd_wrap

# Initialize lookup tables
player_class_tags = {
    'basic_bettor': montecarlo_core.Bettor,
    montecarlo_core.Bettor: 'basic_bettor',
    'basic_banking_bettor': montecarlo_core.BankingBettor,
    montecarlo_core.BankingBettor: 'basic_banking_bettor',
}

game_class_tags = {
    'midnight_craps': games.MidnightCraps,
    games.MidnightCraps: 'midnight_craps',
}

HOMEIP = 'localhost' # "69.247.73.73"
BASEPORT = 5060
try:
    import zmqConstants
    HOMEIP = zmqConstants.HOMEIP
    BASEPORT = zmqConstants.BASEPORT
except ImportError:
    pass

def rcv_wrap(vent):
    """
    Blocks receive while still permitting signal handling
    """
    while True:
        try:
            o = vent.recv_json(zmq.NOBLOCK)  # if we don't use `zmq.NOBLOCK` it will block
                                        # forever, and because zmq is in C, you don't get
                                        # signal handling, i.e. respond to
                                        # Ctrl-C on Windows
        except zmq.ZMQError:
            time.sleep(0.001)  # wait one millisecond before checking again
        else:
            return o


def process_message_in(message):
    """
    takes message dict and returns parameters for play() call.
    will convert tags to objects using global dicts.
    :param message:
    :return:
    """
    player_parameters = message.pop('player_parameters')
    game_parameters = message.pop('game_parameters')
    wager_count = message.pop('wager_count')

    player_class=player_class_tags[player_parameters.pop('player_class')]
    player_parameters['bettor_class'] = player_class
    player_parameters['game'] = game_class_tags[game_parameters['game_name']]
    player_parameters['wager_count'] = wager_count
    return player_parameters


def process_message_out(player_group):
    """
    Takes player group and gets it ready for serialization by replacing class
    objects with tags.
    :param player_group:
    :return:
    """
    for player in player_group:
        player.game = game_class_tags[player.game.__class__]
        player.class_name = player_class_tags[player.__class__]
        player.__dict__['net_worth'] = player.net_worth

    return [player.__dict__ for player in player_group]

def process_message_out_bpf(**kwargs):
    for player in kwargs['player_group']:
        player['net_worth'] = player['current_funds'] + player['bank_balance']

    return kwargs['player_group']

def message_handler_class(message):
    player_parameters = message.pop('player_parameters')
    game_parameters = message.pop('game_parameters')
    wager_count = message.pop('wager_count')
    sample_size = message.pop('sample_size')

    player_class=player_class_tags[player_parameters.pop('player_class')]
    player_parameters['bettor_class'] = player_class
    player_parameters['game'] = game_class_tags[game_parameters['game_name']]
    player_parameters['wager_count'] = wager_count

    player_group = [montecarlo.play(**player_parameters)
                    for _ in range(sample_size)]

    message_out = process_message_out(player_group)
    message_out = montecarlo.calc_stats(message_out)
    return message_out

def message_handler_func(message):
    kwargs = message['bpf_kwargs']
    kwargs = montecarlo_core.basic_player_func(**kwargs)
    # print('*'*300)
    # input()
    message_out = montecarlo.calc_stats_bpf(**kwargs)
    print(message_out)
    # print('\n'*20)
    return message_out

def startup():
    context = zmq.Context()

    print("Building connections.")
    vent = context.socket(zmq.PULL)
    # vent.setsockopt(zmq.RCVBUF, 10)
    # vent.setsockopt(zmq.HWM, 1)

    vent.connect('tcp://{}:{}'.format(HOMEIP, str(BASEPORT + 0)))

    stat_sink = context.socket(zmq.PUSH)
    stat_sink.connect('tcp://{}:{}'.format(HOMEIP, str(BASEPORT + 1)))
    print("Connections complete.")

    start_time = time.time()
    msg_count = 0

    while True:
        message = rcv_wrap(vent)  # this will block forever, which is okay. But it still
                                  # permits signal handling.

        try:
            message['bpf_kwargs']
        except KeyError:
            message_out = message_handler_class(message)
        else:
            message_out = message_handler_func(message)

        snd_wrap(stat_sink.send_json, message_out)
        # pprint(player_group[0].__dict__)

        print("Task #{} complete.".format(msg_count))
        msg_count += 1
        if not msg_count % 100:
            end_time = time.time()
            elapsed = end_time - start_time
            msg_rate = round(msg_count / elapsed, 3)
            print('Processed {} messages per second'.format(msg_rate))
            start_time = end_time
            msg_count = 0


if __name__ == '__main__':
    startup()