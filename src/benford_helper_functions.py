import numpy as np
import pandas as pd
from numba import njit, objmode
from scipy.fft import fft, fftfreq, fftshift, ifft
from scipy.integrate import simps
from scipy.stats import iqr

from NIST_tests import RNG_test
from random_helper_functions import binary_tree_walk, get_bitstring
from stat_tests import chi2_test, ks_test


def benford(d):
    """Benford's law."""
    return np.log10(d + 1) - np.log10(d)


def _get_first_digit(num):
    """By element helper."""
    s = f"{np.abs(num):.12e}"
    return int(s[0])


def get_first_digit(num_arr):
    """Get first digit by Python's f string."""
    return np.vectorize(_get_first_digit)(num_arr)


@njit
def _first_n_digits(num, n):
    return num // 10 ** (int(np.log10(num)) - n + 1)


@njit
def first_n_digits(arr, n):
    """for int only"""
    res = np.zeros(len(arr))
    for i, a in enumerate(arr):
        res[i] = _first_n_digits(a, n)
    return res


def check_benford_scaling(arr, f=1.01, n=1000):
    """Ones scaling test. Iteratively check for scale invariance. Uses ones. Result should be around 0.301."""
    ones_count = np.zeros(n)
    old_arr = arr.copy()

    for i in range(n):
        new_arr = old_arr * f
        first_digits = np.vectorize(get_first_digit)(new_arr)
        _, uniq = np.unique(first_digits, return_counts=True)
        ones_count[i] = uniq[0]
        old_arr = new_arr.copy()

    return ones_count


def normalize(y, x):
    """Normalizes distribution."""
    int_func = simps(y, x)
    return y / int_func


@njit
def make_sampling_function(pts, start=-70, stop=70):
    """Makes step like sampling function that isolates numbers starting with 1."""
    sf_func = np.zeros(len(pts))

    a, b = 0.1, 0.2 - 1e-6

    with objmode(scale="f8[:]"):
        scale = np.logspace(start, stop, np.abs(start) + np.abs(stop) + 1)

    sf = np.zeros((len(scale), 2))
    for i, s in enumerate(scale):
        sf[i, 0] = a * s
        sf[i, 1] = b * s

    sf = np.log10(sf)

    for i, p in enumerate(pts):
        comp = sf < p
        ind_, _ = np.where(comp)

        if comp[ind_[-1]].all() == False:
            sf_func[i] = 1

    return sf_func


def shift_multiply_integrate(log_input, f, n_shift, n_bins=None):
    """Ones scaling test using sampling function and integration.

    Parameters
    ----------
    log_input : np.array
        Data in log10 scale
    f : float
        Scaling factor
    n_shift : int
        Number of shifts
    n_bins : int, optional
        Number of created bins in np.histogram, by default None

    Returns
    -------
    np.array
        Array with ones frequencies.
    """
    integral_results = []
    if n_bins is None:
        n_bins = len(log_input)

    x = log_input
    for n in range(n_shift):
        pdf, bins = np.histogram(x, bins=n_bins, density=True)
        bins = bins[1:]

        sf = make_sampling_function(bins)

        integral = simps(pdf * sf, bins)
        integral_results.append(integral)

        x = log_input + np.log10(f ** (n + 1))

    return integral_results


def shift_multiply_integrate_pdf(x, y, f, n_shift):
    """Same as shift_multiply_integrate but for pdf with bins given by x and values given by y."""
    log_input = x
    integral_results = []

    for n in range(n_shift):
        bins, pdf = x, normalize(y, x)

        sf = make_sampling_function(bins)

        integral = simps(pdf * sf, bins)
        integral_results.append(integral)

        x = log_input + np.log10(f ** (n + 1))

    return integral_results


def benford_ft(pdf, bins, shift=False):
    """Spectral analysis of Bneford's law.

    Parameters
    ----------
    pdf : np.array
        Signal
    bins : np.array
        x-axis, should be in log10 scale
    shift: bool
        Use fftshift, by default False
    """
    N = len(bins)
    dbins = np.diff(np.abs(bins))[0]

    freq = fftfreq(len(bins), dbins)

    sf = make_sampling_function(bins)
    SF = fft(sf) / N

    PDF = fft(pdf)
    PDF /= PDF[0]

    OST = SF * PDF
    ost = np.real(ifft(OST)) * N

    if shift:
        return fftshift(freq), fftshift(SF), sf, fftshift(PDF), fftshift(OST), fftshift(ost)
    else:
        return freq, SF, sf, PDF, OST, ost


def find_nearest(array, value):
    array = np.asarray(array)
    idx = (np.abs(array - value)).argmin()
    return idx


def benfords_test(pdf, bins):
    dbins = np.diff(np.abs(bins))[0]
    freq = fftfreq(len(bins), dbins)

    PDF = fft(pdf)
    PDF /= PDF[0]
    PDF_sig = np.abs(PDF)

    nearest_idx = find_nearest(freq, 1)

    return PDF_sig[nearest_idx]


def construct_log_bins(data, n_bins=None, norm=False):
    if n_bins is None:
        n_bins = len(data)

    bins = np.logspace(np.floor(np.log10(data.min())), np.floor(np.log10(data.max())) + 1, n_bins)

    n, bins = np.histogram(data, bins=bins)
    bins = bins[:-1]
    bins = np.log10(bins)

    if norm:
        pdf = normalize(n, bins)
    else:
        pdf = n

    return pdf, bins


def do_full_rng_test(dists, walk=False, rng_test=True, alpha=0.01, end_bits=None):
    """Count ones, FT test, makes fractions and calculates chi2 and KS, runs NIST tests

    Parameters
    ----------
    dists : np.array or list of np.arrays
        Distributions to test
    walk : bool, optional
        If True use binary_tree_walk to make bit string, by default False
    rng_test : bool, optional
        If False skip NIST test, by default True
    alpha : float, optional
        Statistical significance, by default 0.01
    end_bits : [type], optional
        Number of bits to test in NIST tests, by default None

    Returns
    -------
    tuple
        f1s, first_digits, fracs, chi2_tests, ks_tests, df
        FT of PDF at frequency 1, ratio of ones, "uniformly" distributed fractions, test scores for chi2 and KS, NIST results
    """
    if type(dists) not in [list, np.array]:
        dists = [dists]

    f1s, first_digits, fracs = [], [], []
    rng_tests = []
    chi2_tests, ks_tests = [], []

    for i, lognorm in enumerate(dists):
        print("doing FT test")
        pdf, bins = construct_log_bins(lognorm, norm=True)

        # same as using benfords_test function
        freq, SF, sf, PDF, OST, ost = benford_ft(pdf, bins, shift=True)
        ind = np.argsort(np.abs(SF))
        f1 = np.abs(PDF)[ind[1]]
        f1s.append(f1)

        print("counting first digits")
        first_digit = get_first_digit(lognorm)
        _, c = np.unique(first_digit, return_counts=True)
        c = c / np.sum(c)
        first_digits.append(c)

        print("making fractions")
        frac = np.log10(lognorm) % 1
        fracs.append(frac)

        h = 2 * iqr(frac) * len(frac) ** (-1 / 3)
        n_bins = (frac.max() - frac.min()) / h
        print(f"doing chi2 test, {n_bins}")
        chi2_tests.append(chi2_test(frac, n_bins=int(n_bins), alpha=alpha))
        print("doing ks test")
        ks_tests.append(ks_test(frac, alpha=alpha))

        if rng_test:
            if end_bits is None:
                end_bits = -1

            print("converting to bits")
            if walk:
                bits = binary_tree_walk(frac[:end_bits]).astype(str)
            else:
                bits = get_bitstring(frac[:end_bits], length=32)

            bits = "".join(bits)
            test = RNG_test(bits, short_df=True)
            rng_tests.append(test)
            print(f"{len(bits)} total bits used")

    if rng_test:
        df = pd.concat([i for i in rng_tests])
        df.index = [f"$p_{i}$" for i in range(1, len(df) + 1)]
        df.columns = [i + 1 for i in range(len(df.columns))]
    else:
        df = None

    return f1s, first_digits, fracs, chi2_tests, ks_tests, df


def str_to_bits(st, one_byte=False, remove_spaces=False, to_replace=None):
    """https://stackoverflow.com/questions/18815820/how-to-convert-string-to-binary"""

    if to_replace:
        replaced_lst = []
        for e in list(st.split(" ")):
            if e not in to_replace:
                replaced_lst.append(e)

        st = " ".join(replaced_lst)

    if remove_spaces:
        st = st.replace(" ", "")
        st = st.replace("\n", "")

    if to_replace:
        for r in to_replace:
            st = st.replace(r, "")

    if one_byte:
        return " ".join(format(ord(i), "b").zfill(8) for i in st)
    else:
        return " ".join(format(x, "b") for x in bytearray(st, "utf-8"))
