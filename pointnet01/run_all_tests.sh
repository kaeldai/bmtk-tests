#!/bin/bash
set -e

network_types=(batched individual)

for n in ${network_types[@]}; do
    python test_pointnet.py -n ${n}
    if [[ -x "$(command -v mpirun)" ]]; then
	mpirun -np 2 python test_pointnet.py -n ${n}
    fi
done
