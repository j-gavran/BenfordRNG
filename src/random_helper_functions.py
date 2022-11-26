import bitstring
import numpy as np
from numba import njit
from statsmodels.distributions.empirical_distribution import ECDF


# ECDFs are not used anywhere
def ecdf(a):
    x, counts = np.unique(a, return_counts=True)
    cusum = np.cumsum(counts)
    inv = np.argsort(a)
    cusum = cusum / cusum[-1]
    return x, cusum, inv


def statsmodels_ecdf(a):
    r = ECDF(a)
    return r.x, r.y


@njit
def binary_tree_walk(arr):
    bits = np.zeros(len(arr)).astype(np.int16)
    for i, a in enumerate(arr):
        if a > 0.5:
            bits[i] = 1
    return bits


def _to_bin(num):
    return bin(num)[3:]


def to_bin(nums):
    return np.vectorize(_to_bin)(nums)


def from_bin(num):
    return int(num, 2)


@njit
def bin_str_to_matrix(bin_arr):
    n = len(bin_arr)
    m = int(np.sqrt(n))

    mat = np.zeros((m, m))

    c = 0
    for i in range(m):
        for j in range(m):
            mat[i, j] = bin_arr[c]
            c += 1
    return mat


def split_to_arr(word):
    return np.array([int(char) for char in word])


def save_bin_to_txt(save, name="out.txt"):
    with open(name, "w") as text_file:
        text_file.write(save)


def _float32_to_bin(num, cut):
    int32bits = np.float32(num).view(np.int32).item()
    return "{:032b}".format(int32bits).replace("-", "")[cut:]


def float32_to_bin(nums, cut=0):
    """Note: use get_bitstring."""
    return np.vectorize(_float32_to_bin)(nums, cut)


@njit
def binary_tree_walk(arr):
    bits = np.zeros(len(arr)).astype(np.int16)
    for i, a in enumerate(arr):
        if a > 0.5:
            bits[i] = 1
    return bits


def _bitstring(a, length, cut):
    return bitstring.BitArray(float=a, length=length).bin[cut:]


def get_bitstring(arr, length=32, cut=None):
    """
    https://www.ece.unb.ca/tervo/ee6373/IEEE64.htm
    https://www.h-schmidt.net/FloatConverter/IEEE754.html
    https://stackoverflow.com/questions/16444726/binary-representation-of-float-in-python-bits-not-hex
    """
    if cut is None:
        if length == 64:
            cut = 12
        else:
            cut = 9

    return np.vectorize(_bitstring)(arr, length, cut)
