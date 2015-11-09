__author__ = 'William.George'

from decimal import Decimal as D
import json
from pprint import pprint
import random
import time
import zmq

import montecarlo

try:
    raw_input
except NameError:
    raw_input = input


def snd_wrap(call, data):
    """
    Blocks send while still permitting signal handling
    """
    while True:
        try:
            call(data, zmq.NOBLOCK)  # if we don't use `zmq.NOBLOCK` it will block
                                        # forever, and because zmq is in C, you don't get
                                        # signal handling, i.e. respond to
                                        # Ctrl-C on Windows
        except zmq.ZMQError:
            time.sleep(0.001)  # wait one millisecond before checking again
        else:
            return


def safe_input(rtype, prompt=None):
    """
    Asks for input of requested type until it gets it.
    :param rtype: type
    :param prompt: prompt given to user
    :return: validated input
    """
    if not isinstance(rtype, type):
        raise TypeError('safe_input requires a type')

    if prompt is None:
        prompt = 'Enter a {}'.format(rtype)

    while True:
        user_input = raw_input(prompt)
        try:
            user_input = rtype(user_input)
        except (TypeError, ValueError):
            pass
        else:
            return user_input

default_bpf_kwargs = {
    'game': 'bpf_mg_roulette_thirds',
    'game_sample_size': 5000,
    'rounds_per_game': 150,
    #'progression': False,
    'bank': False,
    'initial_wager': 5,
    'initial_funds': 2000,
    'bank_balance': 0,
    'progression_type': 'ratio', # 'unit' or 'ratio' or None
    'progression_interval': 5,  # set these to zero when not progressing
    'progression_amt': 20,
}

def randomize(kwargs):
    randomize_keys = [
        # 'rounds_per_game',
        'initial_wager',
        'progression_type',
        'progression_interval',
        'progression_amt'
    ]

    for key in randomize_keys:
        if key == 'rounds_per_game':
            val = random.randint(50, 500)
        elif key == 'initial_wager':
            val = random.randint(1, 200)
        elif key == 'progression_type':
            val = random.choice(['unit', 'ratio'])
        elif key == 'progression_interval':
            val = random.randint(1, 20)
        elif key == 'progression_amt':
            val = round(random.uniform(1, 10), 1)
        kwargs[key] = val

    if kwargs['progression_type'] is None:
        kwargs['progression_amt'] = kwargs['progression_interval'] = 0

    return kwargs


def startup():
    context = zmq.Context()

    print("Building connections.")
    worker = context.socket(zmq.PUSH)
    worker.bind('tcp://*:5060')

    stat_sink = context.socket(zmq.PUSH)
    stat_sink.connect('tcp://localhost:5061')
    print("Connections complete.")

    start_time = time.time()
    msg_count = 0
    player_parameters = {
        'player_class': 'basic_bettor',
        'initial_funds': 10000,
        'initial_wager': 10,
    }
    game_parameters = {
        'game_name': 'midnight_craps'
    }
    wager_count = 150
    rolls = []
    sample_size = 100

    namespace = {
        #'player_parameters': player_parameters,
        #'game_parameters': game_parameters,
        #'rolls': rolls,
        #'wager_count': wager_count,
        #'sample_size': sample_size,
        'bpf_kwargs': default_bpf_kwargs
    }
    # namespace['bfp_kwargs'] = randomize(namespace['bpf_kwargs'])
    task_count = 1
    while True:
        if not msg_count % task_count:
            msg_count = 0
            prompt = 'Enter the number of tasks to send.'
            task_count = safe_input(int, prompt)
            start_time = time.time()

        # worker.send_json(namespace)
        namespace['bfp_kwargs'] = randomize(namespace['bpf_kwargs'])
        snd_wrap(worker.send_json, namespace)
        print('Task #{} Sent.'.format(msg_count))

        msg_count += 1
        end_time = time.time()
        elapsed = end_time - start_time
        try:
            msg_rate = round(msg_count / elapsed, 3)
        except ZeroDivisionError:
            msg_rate = 0
        print('Sent {} messages per second'.format(msg_rate))





if __name__ == '__main__':
    startup()