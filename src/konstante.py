import numpy as np
from scipy import constants


def get_constants():
    consts1 = [
        np.pi,
        np.e,
        np.sqrt(2),
        np.sqrt(3),
        1.61803,
        constants.c,
        constants.h,
        constants.hbar,
        constants.epsilon_0,
        constants.mu_0,
        constants.G,
        constants.g,
        constants.e,
        constants.R,
        constants.alpha * 1000,
        constants.N_A,
        constants.k,
        constants.sigma,
        constants.Rydberg,
        constants.m_e,
        constants.m_p,
        constants.m_n,
    ]

    consts1_ = np.array(consts1)

    consts2_ = []
    for k, v in constants.physical_constants.items():
        consts2_.append(v[0])

    consts = np.concatenate((consts1_, consts2_))

    return consts
