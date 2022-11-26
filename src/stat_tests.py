import numpy as np
from scipy.stats import chi2, chisquare, iqr, kstest, kstwo


def chi2_test(data, n_bins=10, alpha=0.01):
    """Chi2 test for uniform distribution.

    Parameters
    ----------
    data : np.array
        Raw data to be hisogramed
    n_bins : int, optional
        Number of bins to use, by default 10
    alpha : float, optional
        Statistical significance, by default 0.01

    Returns
    -------
    tuple of np.array and float
        Array of chi2 test scores and p values, float for critical value at 1 - alpha
    """
    if len(data.shape) == 1:
        data = [data]

    hists, Ns = [], []

    for d in data:
        if n_bins is None:
            h = 2 * iqr(d) * len(d) ** (-1 / 3)
            n_bins = (d.max() - d.min()) / h

        n, _ = np.histogram(d, bins=n_bins)
        hists.append(n)
        Ns.append(np.sum(n))

    results = np.zeros((len(hists), 2))
    for i, (hist, N) in enumerate(zip(hists, Ns)):
        test, p = chisquare(hist, f_exp=N / n_bins)
        results[i, 0], results[i, 1] = test, p

    critical_value = chi2.ppf(1 - alpha, n_bins)

    return results, critical_value


def ks_test(data, alpha=0.01):
    """Kolmogorov-Smirnov test for uniform distribution.

    Parameters
    ----------
    data : np.array
        Raw data
    alpha : float, optional
        Statistical significance, by default 0.01

    Returns
    -------
    tuple of two np.arrays
        Array of KS test scores and p values, array of critical values at 1 - alpha (dependent of length of data)
    """
    if len(data.shape) == 1:
        data = [data]

    results = np.zeros((len(data), 2))
    for i, d in enumerate(data):
        test, p = kstest(d, cdf="uniform", alternative="two-sided", args=(0, 1))
        results[i, 0], results[i, 1] = test, p

    critical_values = []
    for d in data:
        critical_value = kstwo.ppf(1 - alpha, len(d))
        critical_values.append(critical_value)

    return results, critical_values
