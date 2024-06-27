import os
import sys
sys.path.append(os.getcwd())
sys.path.append(os.path.join(os.getcwd(), 'utils'))
from configuration import *
import torch
import pprint
import pNN_Power_Aware as pNN
from utils import *

args = parser.parse_args()

for ds in range(13):
    args.DATASET = ds
    args = FormulateArgs(args)
    
    print(f'Training network on device: {args.DEVICE}.')
    MakeFolder(args)
    
    train_loader, datainfo = GetDataLoader(args, 'train')
    valid_loader, datainfo = GetDataLoader(args, 'valid')
    test_loader, datainfo = GetDataLoader(args, 'test')
    pprint.pprint(datainfo)
    
    SetSeed(args.SEED)
    
    setup = f"data_{datainfo['dataname']}_seed_{args.SEED}_Penalty_{args.powerestimator}_Factor_{args.powerbalance}"
    print(f'Training setup: {setup}.')
    
    msglogger = GetMessageLogger(args, setup)
    msglogger.info(f'Training network on device: {args.DEVICE}.')
    msglogger.info(f'Training setup: {setup}.')
    msglogger.info(datainfo)
    
    def PT(pnn, train_loader, valid_loader, args, msglogger, setup):
    
        # Pretraning
        lossfunction = pNN.Lossfunction(args).to(args.DEVICE)
        optimizer = torch.optim.Adam(pnn.GetParam(), lr=args.LR)
        
        pnn, best = train_pnn_progressive(pnn, train_loader, valid_loader, lossfunction, optimizer, args, msglogger, UUID=setup+'_PT')
    
        if best:
            if not os.path.exists(f'{args.savepath}/'):
                os.makedirs(f'{args.savepath}/')
            torch.save(pnn, f'{args.savepath}/pNN_{setup}.model')
            msglogger.info('Pretraining is finished.')
        else:
            msglogger.warning('Time out, further training is necessary.')
        
        return pnn
    
    def FT(train_loader, valid_loader, args, msglogger, setup):
    
        pnn = torch.load(f'{args.savepath}/pNN_{setup}.model')
    
        # Pruning
        msglogger.info('Pruning...')
        print('Pruning...')
        N1, N2, N3, P1, P2, P3 = pnn.pruning
        information = f'{N1} ({P1*100:.2f}%) resistors, {N2} ({P2*100:.2f}%) activations and {N3} ({P3*100:.2f}%) negation circuits are pruned.'
        msglogger.info(information)
        print(information)
    
    
        # Fine Tuning
        lossfunction = pNN.Lossfunction(args).to(args.DEVICE)
        msglogger.info('Fine tuning...')
        optimizer = torch.optim.Adam(pnn.GetParam(), lr=args.LR/10.)
        pnn, best = train_pnn_progressive(pnn, train_loader, valid_loader, lossfunction, optimizer, args, msglogger, UUID=setup+'_FT')
        if best:
            if not os.path.exists(f'{args.savepath}/'):
                os.makedirs(f'{args.savepath}/')
            torch.save(pnn, f'{args.savepath}/pNN_{setup}_FT.model')
            msglogger.info('Fine tuning if finished.')
        else:
            msglogger.warning('Time out, further training is necessary.') 
    
    
    if os.path.isfile(f'{args.savepath}/pNN_{setup}_FT.model'):
        print(f'{setup}_FT exists, skip this training.')
        msglogger.info('Training was already finished.')
    elif os.path.isfile(f'{args.savepath}/pNN_{setup}.model'):
        print(f'{setup} is pretrained, now fine tuning.')
        FT(train_loader, valid_loader, args, msglogger, setup)
    else:
        topology = [datainfo['N_feature']] + args.hidden + [datainfo['N_class']]
        msglogger.info(f'Topology of the network: {topology}.')
    
        pnn = pNN.pNN(topology, args).to(args.DEVICE)
    
        PT(pnn, train_loader, valid_loader, args, msglogger, setup)  
        FT(train_loader, valid_loader, args, msglogger, setup)