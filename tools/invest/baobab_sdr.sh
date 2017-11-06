#!/bin/bash -l

#SBATCH -N 1
#SBATCH -p debug
#SBATCH -t 00:00:10

#SBATCH --export PYTHONPATH=$HOME/invest/lib/python2.7/
#SBATCH --export PYTHONHOME=$HOME/invest

#!SBATCH --export source $HOME/invest/bin/activate

srun -n1 $HOME/invest/bin/python $HOME/workspace/esws/tools/invest/test_invest_sdr_demo.py --local

