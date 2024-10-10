import time
import math
from .checkpoint import *
from .evaluation import *

def train_pnn(nn, train_loader, valid_loader, lossfunction, optimizer, args, logger, current_epoch, UUID='default'):
    start_training_time = time.time()
    
    evaluator = Evaluator(args)
    
    best_valid_loss = math.inf
    patience = 0
    
    early_stop = False
    
    if load_checkpoint(UUID, args.temppath):
        current_epoch, nn, optimizer, best_valid_loss, lossfunction = load_checkpoint(UUID, args.temppath)
        logger.info(f'Restart previous training from {current_epoch} epoch')
        print(f'Restart previous training from {current_epoch} epoch')
        
    for epoch in range(current_epoch, 10**10):
        start_epoch_time = time.time()
        
        msg = ''
        
        for x_train, y_train in train_loader:
            msg += f'hyperparameters in printed neural network for training :\nepoch : {epoch:-6d} |\n'
            
            L_train = lossfunction(nn, x_train, y_train)
            train_acc, train_power = evaluator(nn, x_train, y_train)
            optimizer.zero_grad()
            L_train.backward()
            optimizer.step()

        with torch.no_grad():
            for x_valid, y_valid in valid_loader:
                msg += f'hyperparameters in printed neural network for validation :\nepoch : {epoch:-6d} |\n'
                
                L_valid = lossfunction(nn, x_valid, y_valid)
                valid_acc, valid_power = evaluator(nn, x_valid, y_valid)
        
        logger.debug(msg)
        
        if args.recording:
            record_checkpoint(epoch, nn, L_train, L_valid, UUID, args.recordpath)
            
        if L_valid.item() < best_valid_loss:
            best_valid_loss = L_valid.item()
            save_checkpoint(epoch, nn, optimizer, best_valid_loss, lossfunction, UUID, args.temppath)
            patience = 0
        else:
            patience += 1

        if patience > args.PATIENCE:
            print('Early stop.')
            logger.info('Early stop.')
            early_stop = True
            break
        
        end_epoch_time = time.time()
        end_training_time = time.time()
        if (end_training_time - start_training_time) >= args.TIMELIMITATION*60*60:
            print('Time limination reached.')
            logger.warning('Time limination reached.')
            break

        for g in optimizer.param_groups:
            current_lr = g['lr']
            
        if not epoch % args.report_freq:
            print(f'| Epoch: {epoch:-6d} | Train loss: {L_train.item():.4f} | Valid loss: {L_valid.item():.4f} | Train acc: {train_acc:.4f} | Valid acc: {valid_acc:.4f} |'\
                  f' patience: {patience:-3d} | lr: {current_lr:.3e} | Epoch time: {end_epoch_time-start_epoch_time:.1f} |'\
                  f' Power: {train_power.item():.2e} | lambda: {lossfunction.args.lambda_:.3e} | mu: {lossfunction.args.mu:.3e} |')
            logger.info(f'| Epoch: {epoch:-6d} | Train loss: {L_train.item():.4f} | Valid loss: {L_valid.item():.4f} | Train acc: {train_acc:.4f} | Valid acc: {valid_acc:.4f} |'\
                        f' patience: {patience:-3d} | lr: {current_lr:.3e} | Epoch time: {end_epoch_time-start_epoch_time:.1f} |'\
                        f' Power: {train_power.item():.2e} | lambda: {lossfunction.args.lambda_:.3e} | mu: {lossfunction.args.mu:.3e} |')
        
    _, resulted_nn, _,_ = load_checkpoint(UUID, args.temppath)
    
    if early_stop:
        os.remove(f'{args.temppath}/{UUID}.ckp')

    return resulted_nn, early_stop, optimizer, epoch


def train_pnn_progressive(nn, train_loader, valid_loader, lossfunction, optimizer, args, logger, current_epoch=0, UUID='default'):
    start_training_time = time.time()
    UUID += '_progressive'

    current_lr = math.inf
    
    while current_lr > args.LR_MIN:
        early_stop = False
        
        nn, early_stop, optimizer, current_epoch = train_pnn(nn, train_loader, valid_loader, lossfunction, optimizer, args, logger, current_epoch, UUID)

        if not early_stop:
            nn, early_stop, optimizer, current_epoch = train_pnn(nn, train_loader, valid_loader, lossfunction, optimizer, args, current_epoch, logger, UUID)
        else:
            logger.info(f'load best network to warm start training with lower lr, current epoch {current_epoch}.')
            print(f'load best network to warm start training with lower lr, current epoch {current_epoch}.')
            for g in optimizer.param_groups:
                g['params'] = [p for p in nn.parameters()]
                g['lr'] = g['lr'] * args.LR_DECAY
                current_lr = g['lr']
            logger.info(f'lr update to {current_lr}.')
            
            save_checkpoint(current_epoch, nn, optimizer, math.inf, lossfunction, UUID, args.temppath)

        end_training_time = time.time()
        if (end_training_time - start_training_time) >= args.TIMELIMITATION*60*60:
            print('Time limination reached.')
            logger.warning('Time limination reached.')
            return nn, early_stop
            
    os.remove(f'{args.temppath}/{UUID}.ckp')
    
    return nn, early_stop, lossfunction, current_epoch


def al_train_pnn_progressive(nn, train_loader, valid_loader, lossfunction, optimizer, args, logger, UUID='default'):
    start_training_time = time.time()
    UUID += '_AL'
    
    C = math.inf
    N_update = 0
    current_epoch = 0
    
    while C > 0.:
        nn, early_stop, lossfunction, current_epoch = train_pnn_progressive(nn, train_loader, valid_loader, lossfunction, optimizer, args, logger, current_epoch, UUID)
    
        if not early_stop:
            nn, early_stop, lossfunction, current_epoch = train_pnn_progressive(nn, train_loader, valid_loader, lossfunction, optimizer, args, logger, current_epoch, UUID)
        else:
            N_update += 1
            logger.info(f'Training converged, update lambda.')
            print(f'Training converged, update lambda.')
            
            # update lambda
            for x, y in train_loader:
                lossfunction(nn, x, y)
            C = lossfunction.constraint(nn)

            if C > 0.:
                temp = (lossfunction.args.lambda_ + lossfunction.args.mu * lossfunction.constraint(nn)).data.clone()
                if temp <= 0.:
                    lossfunction.args.lambda_ = 0.
                else:
                    lossfunction.args.lambda_ = temp.item()
                
                lossfunction.args.mu *= 1.5
    
                # reset learning inital learning rate
                for g in optimizer.param_groups:
                    g['params'] = [p for p in nn.parameters()]
                    g['lr'] = 5 * args.LR / (N_update + 5)
                    current_lr = g['lr']
                logger.info(f'lr reset to {current_lr}.')
                print(f'lr reset to {current_lr}.')

    return nn, early_stop
    
    # evaluator = Evaluator(args)
    
    # best_valid_loss = math.inf
    
    # for g in optimizer.param_groups:
    #     current_lr = g['lr']
    # patience_al_update = 0
    
    # # lr_update = False
    # early_stop = False
    
    # if load_checkpoint(UUID, args.temppath):
    #     current_epoch, nn, optimizer, best_valid_loss = load_checkpoint(UUID, args.temppath)
    #     for g in optimizer.param_groups:
    #         current_lr = g['lr']
    #         g['params'] = [p for p in nn.parameters()]
    #     logger.info(f'Restart previous training from {current_epoch} epoch with lr: {current_lr}.')
    #     print(f'Restart previous training from {current_epoch} epoch with lr: {current_lr}.')
    # else:
    #     current_epoch = 0
    
    # n_update = 0

    # C = math.inf
    # while(C > 0.):

    #     early_stop = False

    #     for epoch in range(current_epoch, 10**10):
    #         start_epoch_time = time.time()
            
    #         msg = ''
            
    #         for x_train, y_train in train_loader:
    #             msg += f'{current_lr}'
    #             msg += f'hyperparameters in printed neural network for training :\nepoch : {epoch:-6d} |\n'
                
    #             L_train = lossfunction(nn, x_train, y_train)
    #             train_acc, train_power = evaluator(nn, x_train, y_train)
    #             optimizer.zero_grad()
    #             L_train.backward()
    #             optimizer.step()
    #             C = nn.Power - args.POWER

    #         with torch.no_grad():
    #             for x_valid, y_valid in valid_loader:
    #                 msg += f'hyperparameters in printed neural network for validation :\nepoch : {epoch:-6d} |\n'
                    
    #                 L_valid = lossfunction(nn, x_valid, y_valid)
    #                 valid_acc, valid_power = evaluator(nn, x_valid, y_valid)
            
    #         logger.debug(msg)
            
    #         if args.recording:
    #             record_checkpoint(epoch, nn, L_train, L_valid, UUID, args.recordpath)
                
        
    #         if L_valid.item() < best_valid_loss:
    #             best_valid_loss = L_valid.item()
    #             save_checkpoint(epoch, nn, optimizer, best_valid_loss, UUID, args.temppath)
    #             patience_al_update = 0
    #         else:
    #             patience_al_update += 1

    #         if patience_al_update > args.AL_PATIENCE:
    #             patience_al_update = 0
    #             print('Overfits training data, update lambda.')
    #             logger.info('Overfits training data, update lambda.')
                
    #             n_update = n_update + 1
    #             update_lambda(args, nn)
    #             args.phi = np.log(epoch + 1)

