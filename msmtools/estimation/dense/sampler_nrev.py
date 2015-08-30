r"""Transition matrix sampling for non-reversible stochastic matrices.

.. moduleauthor:: B.Trendelkamp-Schroer <benjamin DOT trendelkamp-schroer AT fu-berlin DOT de>

"""
from __future__ import absolute_import

import numpy as np

from msmtools.analysis import stationary_distribution

def update_nrev(alpha, P):
    N = alpha.shape[0]
    for i in range(N):
        P[i, :] = np.random.dirichlet(alpha[i, :])   

class SamplerNonRev:
    def __init__(self, Z):
        """Posterior counts"""
        self.Z = 1.0*Z
        """Alpha parameters for dirichlet sampling"""
        self.alpha = Z + 1.0
        """Initial state from single sample"""
        self.P = np.zeros_like(Z)
        self.update()
        
    def update(self, N=1):
        update_nrev(self.alpha, self.P)

    def sample(self, N=1, return_statdist=False):
        self.update(N=N)
        if return_statdist:
            pi = stationary_distribution(self.P)
            return self.P, pi
        else:
            return self.P
        
    
