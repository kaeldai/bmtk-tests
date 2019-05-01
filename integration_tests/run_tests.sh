#!/bin/bash
set -e

bionet_tests=(bio_14cells bio_450cells bio_450cells_exact)
pointnet_tests=(point_120cells point_450cells point_450glifs)
filternet_tests=(filter_graitings)
popnet_tests=(pop_2pops)

single_process=true
with_mpi=true
n_procs=4

run_all=true
bionet_only=false
pointnet_only=false
popnet_only=false
filternet_only=false

specified_tests=()
while [ "$1" != "" ]; do
    case $1 in
        --mpi-only )
            with_mpi=true
            single_process=false
            shift
            ;;
        --no-mpi )
            with_mpi=false
            single_process=true
            shift
            ;;
        -n | --n_procs )
            shift
            n_procs=$1
            ;;
        --bionet )
            run_all=false
            bionet_only=true
            shift
            ;;
        --pointnet )
            run_all=false
            pointnet_only=true
            shift
            ;;
        --popnet )
            run_all=false
            popnet_only=true
            shift
            ;;
        --filternet )
            run_all=false
            filternet_only=true
            shift
            ;;
        * )
            specified_tests+=(${1%/}) #("$1")
            shift
            ;;
     esac
done

#containsTest () {
#  return 1
#  local e match="$1"
#  shift
#  for e; do
#    [[ "$e" == "$match" ]] && return 0
#  done
#  return 1
#}

containsTest () {
    local seeking=$1
    local array="$2[@]"
    local in=1
    for element in "${!array}"; do
        if [[ $element == $seeking ]]; then
            in=0
            break
        fi
    done
    return $in
}



if $run_all || $bionet_only; then
    for biodir in ${bionet_tests[@]}; do
        if [ ${#specified_tests[@]} -gt 0 ] &&  ! containsTest $biodir specified_tests; then
            continue
        fi

        if $single_process; then
            cd $biodir
            echo ">>>>>>>>>>> RUNNING BIONET TEST ${biodir} <<<<<<<<<<<<<<<<"
            echo ">>> NPROCS = 1 <<<"
            python run_sim.py
            echo ">>> SIMULATION COMPLETED. CHECKING RESULTS <<<"
            cd -
            python validate.py ${biodir}/output_files.json
            echo ">>> SIMULATION PASSED! <<<"
        fi

        if $with_mpi; then
            cd $biodir
            echo ">>>>>>>>>>> RUNNING BIONET TEST ${biodir} <<<<<<<<<<<<<<<<"
            echo ">>> NPROCS = ${n_procs} <<<"
            mpirun -np ${n_procs} nrniv -mpi -python run_sim.py
            echo ">>> SIMULATION COMPLETED. CHECKING RESULTS <<<"
            cd -
            python validate.py ${biodir}/output_files.json
            echo ">>> SIMULATION PASSED! <<<"
        fi
    done
fi

if $run_all || $pointnet_only; then
    for pointdir in ${pointnet_tests[@]}; do
        if [ ${#specified_tests[@]} -gt 0 ] &&  ! containsTest $pointdir specified_tests; then
            continue
        fi

        if $single_process; then
            cd $pointdir
            echo ">>>>>>>>>>> RUNNING POINTNET TEST ${pointdir} <<<<<<<<<<<<<<<<"
            echo ">>> NPROCS = 1 <<<"
            python run_sim.py
            echo ">>> SIMULATION COMPLETED. CHECKING RESULTS <<<"
            cd -
            python validate.py ${pointdir}/output_files.json
            echo ">>> SIMULATION PASSED! <<<"
        fi

        if $with_mpi; then
            cd $pointdir
            echo ">>>>>>>>>>> RUNNING POINTNET TEST ${pointdir} <<<<<<<<<<<<<<<<"
            echo ">>> NPROCS = ${n_procs} <<<"
            mpirun -np ${n_procs} python run_sim.py
            echo ">>> SIMULATION COMPLETED. CHECKING RESULTS <<<"
            cd -
            python validate.py ${pointdir}/output_files.json
            echo ">>> SIMULATION PASSED! <<<"
        fi
    done
fi

if $run_all || $popnet_only; then
    for popdir in ${popnet_tests[@]}; do
        if [ ${#specified_tests[@]} -gt 0 ] &&  ! containsTest $popdir specified_tests; then
            continue
        fi

        cd $popdir
        echo ">>>>>>>>>>> RUNNING POPNET TEST ${popdir} <<<<<<<<<<<<<<<<"
        python run_sim.py
        echo ">>> SIMULATION COMPLETED. CHECKING RESULTS <<<"
        cd -
        python validate.py ${popdir}/output_files.json
        echo ">>> SIMULATION PASSED! <<<"
    done
fi


if $run_all || $filternet_only; then
    for filterdir in ${filternet_tests[@]}; do
        if [ ${#specified_tests[@]} -gt 0 ] &&  ! containsTest $filterdir specified_tests; then
            continue
        fi

        cd $filterdir
        echo ">>>>>>>>>>> RUNNING FILTERNET TEST ${filterdir} <<<<<<<<<<<<<<<<"
        python run_sim.py
        echo ">>> SIMULATION COMPLETED. CHECKING RESULTS <<<"
        cd -
        python validate.py ${filterdir}/output_files.json
        echo ">>> SIMULATION PASSED! <<<"
    done
fi

echo ">>>>> PASSED ALL TESTS <<<<<<<<<"