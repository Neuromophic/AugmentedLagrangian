import numpy as np
import torch
from pLNC import *

# ================================================================================================================================================
# ===============================================================  Printed Layer  ================================================================
# ================================================================================================================================================
class pLayer(torch.nn.Module):
    def __init__(self, n_in, n_out, args, ACT, INV):
        super().__init__()
        self.args = args
        # define nonlinear circuits
        self.INV = INV
        self.ACT = ACT
        self.nin = n_in
        self.nout = n_out
        # initialize conductances for weights
        theta = torch.rand([n_in + 2, n_out])/100. + args.gmin
        theta[-1, :] = theta[-1, :] + args.gmax
        theta[-2, :] = self.ACT.eta[2].detach().item() / \
            (1.-self.ACT.eta[2].detach().item()) * \
            (torch.sum(theta[:-2, :], axis=0)+theta[-1, :])
        self.theta_ = torch.nn.Parameter(theta, requires_grad=True)

        # for 3 masks: 1 --> unchanged; 0 --> changed
        self.theta_mask = torch.ones(theta.shape)
        self.act_mask = torch.ones(n_out).view(1,-1)
        self.inv_mask = torch.ones(n_in + 2).view(-1,1)

        self.pruned = False

    @property
    def pruning_(self):
        n_in = self.theta.shape[0] - 2
        temp_t = self.theta_before_pruning.clone().detach()
        self.theta_mask[temp_t == 0.] = 0.

        temp_a = torch.sum(self.theta_mask[:n_in, :], axis = 0, keepdim=True)
        self.act_mask[temp_a == 0.] = 0.
        self.theta_mask = self.theta_mask * self.act_mask

        negative = torch.zeros(self.theta.shape)
        negative[temp_t < 0.] = 1.
        temp_i = torch.sum(negative[:,:], axis = 1, keepdim = True)
        self.inv_mask[:n_in,:][temp_i[:n_in,:] == 0] = 0.
        self.pruned = True

        num_t = torch.sum(self.theta_mask == 0).item()
        num_a = torch.sum(self.act_mask == 0).item()
        num_i = torch.sum(self.inv_mask == 0).item()

        num_t_m = self.theta_mask.numel()
        num_a_m = self.act_mask.numel()
        num_i_m = self.inv_mask.numel()

        return num_t,num_a,num_i,num_t_m,num_a_m,num_i_m

    @property
    def device(self):
        return self.args.DEVICE

    @property
    def theta_before_pruning(self):
        self.theta_.data.clamp_(-self.args.gmax, self.args.gmax)
        theta_temp = self.theta_.clone()
        theta_temp[theta_temp.abs() < self.args.gmin] = 0.
        return theta_temp.detach() + self.theta_ - self.theta_.detach()

    @property
    def theta(self):
        temp = self.theta_mask * (self.theta_before_pruning)
        relu = torch.nn.ReLU()
        return relu(temp) * (1. - self.inv_mask) + temp * self.inv_mask

    @property
    def W(self):
        return self.theta.abs() / (torch.sum(self.theta.abs(), axis=0, keepdim=True) +  1e-10)

    def MAC(self, a):
        positive = self.theta.clone().to(self.device)
        positive[positive >= 0] = 1.
        positive[positive < 0] = 0.
        negative = 1. - positive
        a_extend = torch.cat([a,
                              torch.ones([a.shape[0], 1]).to(self.device),
                              torch.zeros([a.shape[0], 1]).to(self.device)], dim=1)
        a_neg = self.INV(a_extend)
        a_neg[:, -1] = 0.
        z = torch.matmul(a_extend, self.W * positive) + \
            torch.matmul(a_neg, self.W * negative)
        return z

    def forward(self, a_previous):
        z_new = self.MAC(a_previous)
        self.mac_power = self.MACPower(a_previous, z_new)
        a_new = self.ACT(z_new) * self.act_mask
        self.act_power = self.ACT.power * torch.sum(self.act_mask)
        return a_new

    @property
    def g_tilde(self):
        # scaled conductances
        g_initial = self.theta_.abs()
        g_min = g_initial.min(dim=0, keepdim=True)[0]
        scaler = self.args.pgmin / g_min
        return g_initial * scaler

    def MACPower(self, x, y):
        x_extend = torch.cat([x,
                              torch.ones([x.shape[0], 1]).to(self.device),
                              torch.zeros([x.shape[0], 1]).to(self.device)], dim=1)
        x_neg = self.INV(x_extend)
        x_neg[:, -1] = 0.

        E = x_extend.shape[0]
        M = x_extend.shape[1]
        N = y.shape[1]

        positive = self.theta.clone().detach().to(self.device)
        positive[positive >= 0] = 1.
        positive[positive < 0] = 0.
        negative = 1. - positive

        Power = torch.tensor(0.).to(self.device)

        for m in range(M):
            for n in range(N):
                Power += self.g_tilde[m, n] * (
                    (x_extend[:, m]*positive[m, n]+x_neg[:, m]*negative[m, n])-y[:, n]).pow(2.).sum()
        Power = Power / E
        return Power
    
    # @property
    # def neg_power(self):
    #     # forward pass: power of neg * number of negative weights
    #     positive = self.theta.clone().detach()[:-1,:]
    #     positive[positive >= 0] = 1.
    #     positive[positive <  0] = 0.
    #     negative = 1. - positive
    #     N_neg = negative.sum(1)
    #     N_neg[N_neg>0] = 1.
    #     N_neg = N_neg.sum()
    #     power = self.INV.power * N_neg
    #     # backward pass: power of neg * value of negative weights
    #     soft_count = 1 - torch.sigmoid(self.theta[:-1,:])
    #     soft_count = soft_count * negative
    #     soft_count = soft_count.max(1)[0].sum()
    #     power_relaxed = self.INV.power * soft_count
    #     if not self.pruned:
    #         return power.detach() + power_relaxed - power_relaxed.detach()
    #     else:
    #         return power

    @property
    def soft_num_theta(self):
        # forward pass: number of theta
        nonzero = self.theta.clone().detach().abs()
        nonzero[nonzero > 0] = 1.
        N_theta = nonzero.sum()
        # backward pass: pvalue of the minimal negative weights
        soft_count = torch.sigmoid(self.theta.abs())
        soft_count = soft_count * nonzero
        soft_count = soft_count.sum()
        if not self.pruned:
            return N_theta.detach() + soft_count - soft_count.detach()
        else:
            return N_theta

    @property
    def soft_num_act(self):
        # forward pass: number of act
        nonzero = self.theta.clone().detach().abs()[:-2, :]
        nonzero[nonzero > 0] = 1.
        N_act = nonzero.max(0)[0].sum()
        # backward pass: pvalue of the minimal negative weights
        soft_count = torch.sigmoid(self.theta.abs()[:-2, :])
        soft_count = soft_count * nonzero
        soft_count = soft_count.max(0)[0].sum()
        if not self.pruned:
            return N_act.detach() + soft_count - soft_count.detach()
        else:
            return N_act

    @property
    def soft_num_neg(self):
        # forward pass: number of negative weights
        positive = self.theta.clone().detach()[:-2, :]
        positive[positive >= 0] = 1.
        positive[positive < 0] = 0.
        negative = 1. - positive
        N_neg = negative.max(1)[0].sum()
        # backward pass: pvalue of the minimal negative weights
        soft_count = 1 - torch.sigmoid(self.theta[:-2, :])
        soft_count = soft_count * negative
        soft_count = soft_count.max(1)[0].sum()
        if not self.pruned:
            return N_neg.detach() + soft_count - soft_count.detach()
        else:
            return N_neg
    
    # @property
    # def power(self):
    #     return self.mac_power + self.act_power + self.neg_power

    # def WeightAttraction(self):
    #     mean = self.theta.mean(dim=0)
    #     diff = self.theta - mean
    #     return diff.pow(2.).mean()

    # def WeightDecay(self):
    #     return self.theta.pow(2.).mean()

    # def SetParameter(self, name, value):
    #     if name == 'args':
    #         self.args = value
    #         self.INV.args = value
    #         self.ACT.args = value

    def UpdateArgs(self, args):
        self.args = args


# ================================================================================================================================================
# ==============================================================  Printed Circuit  ===============================================================
# ================================================================================================================================================
class pNN(torch.nn.Module):
    def __init__(self, topology, args):
        super().__init__()

        self.args = args
        # define nonlinear circuits
        self.act = TanhRT(args)
        self.inv = InvRT(args)

        self.model = torch.nn.Sequential()
        for i in range(len(topology)-1):
            self.model.add_module(
                f'{i}-th pLayer', pLayer(topology[i], topology[i+1], args, self.act, self.inv))

    def forward(self, X):
        return self.model(X)
    
    @property
    def pruning(self):
        result = (0,0,0,0,0,0)
        for layer in self.model:
            result = tuple(a+b for a,b in zip(result,layer.pruning_))

        return result[0], result[1], result[2], result[0]/result[3], result[1]/result[4], result[2]/result[5]

    @property
    def device(self):
        return self.args.DEVICE
    
    @property
    def soft_count_neg(self):
        soft_count = torch.tensor([0.]).to(self.device)
        for l in self.model:
            if hasattr(l, 'soft_num_neg'):
                soft_count += l.soft_num_neg
        return soft_count

    @property
    def soft_count_act(self):
        soft_count = torch.tensor([0.]).to(self.device)
        for l in self.model:
            if hasattr(l, 'soft_num_act'):
                soft_count += l.soft_num_act
        return soft_count

    @property
    def soft_count_theta(self):
        soft_count = torch.tensor([0.]).to(self.device)
        for l in self.model:
            if hasattr(l, 'soft_num_theta'):
                soft_count += l.soft_num_theta
        return soft_count

    @property
    def power_neg(self):
        return self.inv.power * self.soft_count_neg

    @property
    def power_act(self):
        return self.act.power * self.soft_count_act

    @property
    def power_mac(self):
        power_mac = torch.tensor([0.]).to(self.device)
        for l in self.model:
            if hasattr(l, 'mac_power'):
                power_mac += l.mac_power
        return power_mac
    
    @property
    def Power(self):
        return self.power_neg + self.power_act + self.power_mac

    def GetParam(self):
        weights = [p for name, p in self.named_parameters() if name.endswith('theta_') or name.endswith('beta')]
        nonlinear = [p for name, p in self.named_parameters() if name.endswith('rt_')]
        if self.args.lnc:
            return weights + nonlinear
        else:
            return weights

    def UpdateArgs(self, args):
        self.args = args
        self.act.args = args
        self.inv.args = args
        for layer in self.model:
            if hasattr(layer, 'UpdateArgs'):
                layer.UpdateArgs(args)

# ================================================================================================================================================
# ===============================================================  Loss function  ================================================================
# ================================================================================================================================================

class Lossfunction(torch.nn.Module):
    def __init__(self, args):
        super().__init__()
        self.args = args

    def standard(self, prediction, label):
        celoss = torch.nn.CrossEntropyLoss()
        return celoss(prediction, label)

    def PowerEstimator(self, nn, x):
        _ = nn(x)
        return nn.Power

    def forward(self, nn, x, label):
        if self.args.powerestimator == 'power':
            return (1. - self.args.powerbalance) * self.standard(nn(x), label) + self.args.powerbalance * self.PowerEstimator(nn, x)
        elif self.args.powerestimator == 'AL':
            return None
