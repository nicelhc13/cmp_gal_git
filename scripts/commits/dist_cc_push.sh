#!/bin/bash

# execute cc_push of dist-app

ITER_NO=3
THREAD_NO=56
GRAPHS=(
        "friendster"
        "webGraph"
        "road-usad"
        "twitter"
        "socLive")

for iter in {0..$ITER_NO};
do
    for graph in ${GRAPHS[@]}; do
        echo bin/cc_push paper_inputs/${graph}_galois.gr -t=${THREAD_NO} -symmetricGraph
        ./bin/cc_push paper_inputs/${graph}_galois.csgr -t=$THREAD_NO -symmetricGraph >> cc_push_results_03
    done
done 
