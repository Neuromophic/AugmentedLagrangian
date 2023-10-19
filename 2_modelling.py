#!/usr/bin/env python
#SBATCH --job-name=AUGLAG
#SBATCH --error=%x.%j.err
#SBATCH --output=%x.%j.out
#SBATCH --mail-user=hzhao@teco.edu
#SBATCH --export=ALL
#SBATCH --time=48:00:00
#SBATCH --partition=sdil
#SBATCH --gres=gpu:1

import os
import sys
sys.path.append(os.getcwd())
sys.path.append(os.path.join(os.getcwd(), 'utils'))
import torch
import training
import config
import matplotlib.pyplot as plt
import os

seed = int(sys.argv[1])
lr   = int(sys.argv[2])
for num_layer in range(2,10):
    for num_neuron in range(2,10):

        exp_setup = f'{num_layer}_{num_neuron}_{lr}_{seed}'
        print(f'The experiment setup is {exp_setup}.')

        if os.path.exists(f'./NNs/constrainter_{exp_setup}'):
            pass
        else:
            loaders = torch.load('constraint_data.loader')
            train_loader, valid_loader, test_loader = loaders['train'], loaders['valid'], loaders['test']

            hiddens = [num_neuron for i in range(num_layer-1)]

            topology = [2] + hiddens + [1]

            config.SetSeed(seed)
            model = torch.nn.Sequential()
            for t in range(len(topology)-1):
                model.add_module(f'{t}-MAC', torch.nn.Linear(topology[t], topology[t+1]))
                model.add_module(f'{t}-ACT', torch.nn.PReLU())

            lossfunction = torch.nn.MSELoss()
            optimizer = torch.optim.Adam(model.parameters(), lr=10**lr)

            model, train_loss, valid_loss = training.train_nn(model, train_loader, valid_loader, lossfunction, optimizer, UUID=exp_setup)
            torch.save(model, f'./NNs/constrainter_{exp_setup}')

            plt.figure()
            plt.plot(train_loss, label='train')
            plt.plot(valid_loss, label='valid')
            plt.savefig(f'./NNs/train_curve_{exp_setup}.pdf', format='pdf', bbox_inches='tight')
