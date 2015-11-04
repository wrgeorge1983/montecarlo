__author__ = 'William.George'

from csv import DictWriter
from decimal import Decimal as D
import json
from pprint import pprint
import time
from queue import Queue
import zmq

from montecarlo import calc_stats, print_stats
from zmqWorker import rcv_wrap
from zmqVent import snd_wrap, safe_input


output_filename = 'stats.csv'
output_fieldnames = [
    'class_name',
    'wager_count',
    'initial_funds',
    'initial_wager',
    'lose_multiple',
    'members',
    'dead',
    'death_rate',
    'avg_nw',
    'avg_nb_nw',
    'profit_rate',
    'avg_p_nw',
]


def write_out(stats_list):
        """
        writes stats to CSV
        :param stats_list: list of dicts
        :return:
        """
        with open(output_filename, 'a') as output_file:
            writer = DictWriter(output_file,
                                fieldnames=output_fieldnames,
                                delimiter=',',
                                extrasaction='ignore',
                                lineterminator='\n')
            writer.writerows(stats_list)
        print('Wrote {} lines to {}'.format(len(stats_list), output_filename))


def startup():
    context = zmq.Context()

    print("Building connections.")
    worker = context.socket(zmq.PULL)
    worker.bind('tcp://*:5061')

    # sink = context.socket(zmq.PUSH)
    # sink.connect('tcp://localhost:5559')
    print("Connections complete.")

    start_time = time.time()
    msg_count = 0
    last_write = start_time
    output_queue = []

    while True:
        message = rcv_wrap(worker)  # should block but still permit
                                    # signal handling.

        stats = calc_stats(message)

        output_queue.append(stats)
        curtime = time.time()
        msg_count += 1
        if ((curtime - last_write) > 5) and output_queue:
            write_out(output_queue)
            output_queue = []
            last_write = curtime
            elapsed = curtime - start_time
            msg_rate = round(msg_count / elapsed, 3)
            print('processed {:.3} messages per second'.format(msg_rate))
            start_time = curtime
            msg_count = 0


if __name__ == '__main__':
    startup()