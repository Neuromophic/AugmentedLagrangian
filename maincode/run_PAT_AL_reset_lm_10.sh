#!/bin/bash

#SBATCH --partition=single
#SBATCH --ntasks-per-node=40
#SBATCH --time=72:00:00
#SBATCH --job-name=PAT_AL_reset_lm
#SBATCH --error=%x.%j.err
#SBATCH --output=%x.%j.out
#SBATCH --mail-user=hzhao@teco.edu

python3 experiment-Copy1.py --DATASET 09 --SEED 00 --powerestimator AL --POWER 280 --projectname PowerAwareAugmentedLagrangian &
python3 experiment-Copy1.py --DATASET 09 --SEED 01 --powerestimator AL --POWER 280 --projectname PowerAwareAugmentedLagrangian &
python3 experiment-Copy1.py --DATASET 09 --SEED 02 --powerestimator AL --POWER 280 --projectname PowerAwareAugmentedLagrangian &
python3 experiment-Copy1.py --DATASET 09 --SEED 03 --powerestimator AL --POWER 280 --projectname PowerAwareAugmentedLagrangian &
python3 experiment-Copy1.py --DATASET 09 --SEED 04 --powerestimator AL --POWER 280 --projectname PowerAwareAugmentedLagrangian &
python3 experiment-Copy1.py --DATASET 09 --SEED 05 --powerestimator AL --POWER 280 --projectname PowerAwareAugmentedLagrangian &
python3 experiment-Copy1.py --DATASET 09 --SEED 06 --powerestimator AL --POWER 280 --projectname PowerAwareAugmentedLagrangian &
python3 experiment-Copy1.py --DATASET 09 --SEED 07 --powerestimator AL --POWER 280 --projectname PowerAwareAugmentedLagrangian &
python3 experiment-Copy1.py --DATASET 09 --SEED 08 --powerestimator AL --POWER 280 --projectname PowerAwareAugmentedLagrangian &
python3 experiment-Copy1.py --DATASET 09 --SEED 09 --powerestimator AL --POWER 280 --projectname PowerAwareAugmentedLagrangian &
python3 experiment-Copy1.py --DATASET 09 --SEED 00 --powerestimator AL --POWER 560 --projectname PowerAwareAugmentedLagrangian &
python3 experiment-Copy1.py --DATASET 09 --SEED 01 --powerestimator AL --POWER 560 --projectname PowerAwareAugmentedLagrangian &
python3 experiment-Copy1.py --DATASET 09 --SEED 02 --powerestimator AL --POWER 560 --projectname PowerAwareAugmentedLagrangian &
python3 experiment-Copy1.py --DATASET 09 --SEED 03 --powerestimator AL --POWER 560 --projectname PowerAwareAugmentedLagrangian &
python3 experiment-Copy1.py --DATASET 09 --SEED 04 --powerestimator AL --POWER 560 --projectname PowerAwareAugmentedLagrangian &
python3 experiment-Copy1.py --DATASET 09 --SEED 05 --powerestimator AL --POWER 560 --projectname PowerAwareAugmentedLagrangian &
python3 experiment-Copy1.py --DATASET 09 --SEED 06 --powerestimator AL --POWER 560 --projectname PowerAwareAugmentedLagrangian &
python3 experiment-Copy1.py --DATASET 09 --SEED 07 --powerestimator AL --POWER 560 --projectname PowerAwareAugmentedLagrangian &
python3 experiment-Copy1.py --DATASET 09 --SEED 08 --powerestimator AL --POWER 560 --projectname PowerAwareAugmentedLagrangian &
python3 experiment-Copy1.py --DATASET 09 --SEED 09 --powerestimator AL --POWER 560 --projectname PowerAwareAugmentedLagrangian &
python3 experiment-Copy1.py --DATASET 09 --SEED 00 --powerestimator AL --POWER 840 --projectname PowerAwareAugmentedLagrangian &
python3 experiment-Copy1.py --DATASET 09 --SEED 01 --powerestimator AL --POWER 840 --projectname PowerAwareAugmentedLagrangian &
python3 experiment-Copy1.py --DATASET 09 --SEED 02 --powerestimator AL --POWER 840 --projectname PowerAwareAugmentedLagrangian &
python3 experiment-Copy1.py --DATASET 09 --SEED 03 --powerestimator AL --POWER 840 --projectname PowerAwareAugmentedLagrangian &
python3 experiment-Copy1.py --DATASET 09 --SEED 04 --powerestimator AL --POWER 840 --projectname PowerAwareAugmentedLagrangian &
python3 experiment-Copy1.py --DATASET 09 --SEED 05 --powerestimator AL --POWER 840 --projectname PowerAwareAugmentedLagrangian &
python3 experiment-Copy1.py --DATASET 09 --SEED 06 --powerestimator AL --POWER 840 --projectname PowerAwareAugmentedLagrangian &
python3 experiment-Copy1.py --DATASET 09 --SEED 07 --powerestimator AL --POWER 840 --projectname PowerAwareAugmentedLagrangian &
python3 experiment-Copy1.py --DATASET 09 --SEED 08 --powerestimator AL --POWER 840 --projectname PowerAwareAugmentedLagrangian &
python3 experiment-Copy1.py --DATASET 09 --SEED 09 --powerestimator AL --POWER 840 --projectname PowerAwareAugmentedLagrangian &
python3 experiment-Copy1.py --DATASET 09 --SEED 00 --powerestimator AL --POWER 1120 --projectname PowerAwareAugmentedLagrangian &
python3 experiment-Copy1.py --DATASET 09 --SEED 01 --powerestimator AL --POWER 1120 --projectname PowerAwareAugmentedLagrangian &
python3 experiment-Copy1.py --DATASET 09 --SEED 02 --powerestimator AL --POWER 1120 --projectname PowerAwareAugmentedLagrangian &
python3 experiment-Copy1.py --DATASET 09 --SEED 03 --powerestimator AL --POWER 1120 --projectname PowerAwareAugmentedLagrangian &
python3 experiment-Copy1.py --DATASET 09 --SEED 04 --powerestimator AL --POWER 1120 --projectname PowerAwareAugmentedLagrangian &
python3 experiment-Copy1.py --DATASET 09 --SEED 05 --powerestimator AL --POWER 1120 --projectname PowerAwareAugmentedLagrangian &
python3 experiment-Copy1.py --DATASET 09 --SEED 06 --powerestimator AL --POWER 1120 --projectname PowerAwareAugmentedLagrangian &
python3 experiment-Copy1.py --DATASET 09 --SEED 07 --powerestimator AL --POWER 1120 --projectname PowerAwareAugmentedLagrangian &
python3 experiment-Copy1.py --DATASET 09 --SEED 08 --powerestimator AL --POWER 1120 --projectname PowerAwareAugmentedLagrangian &
python3 experiment-Copy1.py --DATASET 09 --SEED 09 --powerestimator AL --POWER 1120 --projectname PowerAwareAugmentedLagrangian &

wait
