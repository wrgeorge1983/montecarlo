#!/bin/bash
for i in `seq 1 $1`;
do
    python zmqWorker.py &
done