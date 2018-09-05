#!/bin/bash
set -e

input_types=(virt iclamp xstim)
connection_types=(nsyns sections)

for i in ${input_types[@]}; do
    for c in ${connection_types[@]}; do
	python test_bionet.py -i ${i} -c ${c}
	if [[ -x "$(command -v mpirun)" ]]; then
	    mpirun -np 4 nrniv -mpi -python test_bionet.py -i ${i} -c ${c}
	fi
    done
done

