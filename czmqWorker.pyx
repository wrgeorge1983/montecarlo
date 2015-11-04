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


def startup():
    context = zmq.Context()

    print("Building connections.")
    vent = context.socket(zmq.PULL)
    vent.connect('tcp://161.217.106.6:5060')

    stat_sink = context.socket(zmq.PUSH)
    stat_sink.connect('tcp://161.217.106.6:5061')
    print("Connections complete.")

    start_time = time.time()
    msg_count = 0

    while True:
        message = rcv_wrap(vent)  # this will block forever, which is okay. But it still
                                  # permits signal handling.
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