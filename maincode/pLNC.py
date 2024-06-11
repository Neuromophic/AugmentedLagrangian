import numpy as np
import torch

# ================================================================================================================================================
# =====================================================  Learnable Negative Weight Circuit  ======================================================
# ================================================================================================================================================

class InvRT(torch.nn.Module):
    def __init__(self, args):
        super().__init__()
        self.args = args
        # R1, R2, R3, W1, L1, W2, L2, W3, L3
        self.rt_ = torch.nn.Parameter(torch.tensor([args.NEG_R1n, args.NEG_R2n, args.NEG_R3n, args.NEG_W1n, args.NEG_L1n, args.NEG_W2n, args.NEG_L2n, args.NEG_W3n, args.NEG_L3n]).to(args.DEVICE), requires_grad=True)
        # model
        package = torch.load('./utils/neg_param.package')
        self.eta_estimator = package['eta_estimator'].to(self.DEVICE)
        self.eta_estimator.train(False)
        for name, param in self.eta_estimator.named_parameters():
            param.requires_grad = False
        self.X_max = package['X_max'].to(self.DEVICE)
        self.X_min = package['X_min'].to(self.DEVICE)
        self.Y_max = package['Y_max'].to(self.DEVICE)
        self.Y_min = package['Y_min'].to(self.DEVICE)
        # load power model
        package = torch.load('./utils/neg_power.package')
        self.power_estimator = package['power_estimator'].to(self.DEVICE)
        for name, param in self.power_estimator.named_parameters():
            param.requires_grad = False
        self.power_estimator.train(False)
        self.pow_X_max = package['X_max'].to(self.DEVICE)
        self.pow_X_min = package['X_min'].to(self.DEVICE)
        self.pow_Y_max = package['Y_max'].to(self.DEVICE)
        self.pow_Y_min = package['Y_min'].to(self.DEVICE)

    @property
    def DEVICE(self):
        return self.args.DEVICE
    
    @property
    def RT(self):
        # keep values in (0,1)
        rt_temp = torch.sigmoid(self.rt_)
        RTn = torch.zeros([12]).to(self.DEVICE)
        RTn[:9] = rt_temp
        # denormalization
        RT = RTn * (self.X_max - self.X_min) + self.X_min
        return RT

    @property
    def RTn_extend(self):
        RT_extend = torch.stack([self.RT[0], self.RT[1], self.RT[2], self.RT[3],
                                 self.RT[4], self.RT[5], self.RT[6], self.RT[7],
                                 self.RT[8], self.RT[3]/self.RT[4], self.RT[5]/self.RT[6],
                                 self.RT[7]/self.RT[8]])
        return (RT_extend - self.X_min) / (self.X_max - self.X_min)

    @property
    def eta(self):
        # calculate eta
        eta_n = self.eta_estimator(self.RTn_extend)
        eta = eta_n * (self.Y_max - self.Y_min) + self.Y_min
        return eta

    @property
    def power(self):
        # calculate power
        power_n = self.power_estimator(self.RTn_extend)
        power = power_n * (self.pow_Y_max - self.pow_Y_min) + self.pow_Y_min
        return power.mean()

    def forward(self, z):
        a = - (self.eta[0] + self.eta[1] * torch.tanh((z - self.eta[2]) * self.eta[3]))
        return a
    
    def UpdateArgs(self, args):
        self.args = args
    

# ================================================================================================================================================
# ========================================================  Learnable Activation Circuit  ========================================================
# ================================================================================================================================================

class TanhRT(torch.nn.Module):
    def __init__(self, args):
        super().__init__()
        self.args = args
        # R1n, R2n, W1n, L1n, W2n, L2n
        self.rt_ = torch.nn.Parameter(
            torch.tensor([args.ACT_R1n, args.ACT_R2n, args.ACT_W1n, args.ACT_L1n, args.ACT_W2n, args.ACT_L2n]), requires_grad=True)

        # model
        package = torch.load('./utils/act_model_package')
        self.eta_estimator = package['eta_estimator'].to(self.DEVICE)
        self.eta_estimator.train(False)
        for n, p in self.eta_estimator.named_parameters():
            p.requires_grad = False
        self.X_max = package['X_max'].to(self.DEVICE)
        self.X_min = package['X_min'].to(self.DEVICE)
        self.Y_max = package['Y_max'].to(self.DEVICE)
        self.Y_min = package['Y_min'].to(self.DEVICE)
        # load power model
        package = torch.load('./utils/act_power_model_package')
        self.power_estimator = package['power_estimator'].to(self.DEVICE)
        self.power_estimator.train(False)
        for n, p in self.power_estimator.named_parameters():
            p.requires_grad = False
        self.pow_X_max = package['X_max'].to(self.DEVICE)
        self.pow_X_min = package['X_min'].to(self.DEVICE)
        self.pow_Y_max = package['Y_max'].to(self.DEVICE)
        self.pow_Y_min = package['Y_min'].to(self.DEVICE)

    @property
    def DEVICE(self):
        return self.args.DEVICE
    
    @property
    def RT(self):
        # keep values in (0,1)
        rt_temp = torch.sigmoid(self.rt_)
        RTn = torch.zeros([9]).to(self.DEVICE)
        RTn[:6] = rt_temp
        # denormalization
        RT = RTn * (self.X_max - self.X_min) + self.X_min
        return RT
    
    
    @property
    def RTn_extend(self):
        RT_extend = torch.stack([self.RT[0], self.RT[1], self.RT[2], self.RT[3],
                                 self.RT[4], self.RT[5], self.RT[1]/self.RT[0],
                                 self.RT[3]/self.RT[2], self.RT[5]/self.RT[4]])
        return (RT_extend - self.X_min) / (self.X_max - self.X_min)

    @property
    def eta(self):
        # calculate eta
        eta_n = self.eta_estimator(self.RTn_extend)
        eta = eta_n * (self.Y_max - self.Y_min) + self.Y_min
        return eta

    @property
    def power(self):
        # calculate power
        power_n = self.power_estimator(self.RTn_extend)
        power = power_n * (self.pow_Y_max - self.pow_Y_min) + self.pow_Y_min
        return power.mean()

    def forward(self, z):
        a = self.eta[0] + self.eta[1] * torch.tanh((z - self.eta[2]) * self.eta[3])
        return a
    
    def UpdateArgs(self, args):
        self.args = args
    