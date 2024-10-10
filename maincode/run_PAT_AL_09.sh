#!/bin/bash

#SBATCH --partition=single
#SBATCH --ntasks-per-node=1
#SBATCH --time=72:00:00
#SBATCH --job-name=PAT_AL
#SBATCH --error=%x.%j.err
#SBATCH --output=%x.%j.out
#SBATCH --mail-user=hzhao@teco.edu

python3 experiment.py --DATASET 08 --SEED 01 --powerestimator AL --POWER 600 --projectname PowerAwareAugmentedLagrangian &

wait