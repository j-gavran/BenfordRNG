# https://github.com/stevenang/randomness_testsuite
import os

import numpy as np
from tqdm import tqdm

from ApproximateEntropy import ApproximateEntropy as aet
from Complexity import ComplexityTest as ct
from CumulativeSum import CumulativeSums as cst
from FrequencyTest import FrequencyTest as ft
from Matrix import Matrix as mt
from RandomExcursions import RandomExcursions as ret
from RunTest import RunTest as rt
from Serial import Serial as serial
from Spectral import SpectralTest as st
from TemplateMatching import TemplateMatching as tm
from Universal import Universal as ut

test_type = [
    "01. Frequency Test (Monobit)",
    "02. Frequency Test within a Block",
    "03. Run Test",
    "04. Longest Run of Ones in a Block",
    "05. Binary Matrix Rank Test",
    "06. Discrete Fourier Transform (Spectral) Test",
    "07. Non-Overlapping Template Matching Test",
    "08. Overlapping Template Matching Test",
    "09. Maurer's Universal Statistical test",
    "10. Linear Complexity Test",
    "11. Serial test",
    "12. Approximate Entropy Test",
    "13. Cummulative Sums (Forward) Test",
    "14. Cummulative Sums (Reverse) Test",
    "15. Random Excursions Test",
    "16. Random Excursions Variant Test",
]

test_function = {
    0: ft.monobit_test,
    1: ft.block_frequency,
    2: rt.run_test,
    3: rt.longest_one_block_test,
    4: mt.binary_matrix_rank_text,
    5: st.sepctral_test,
    6: tm.non_overlapping_test,
    7: tm.overlapping_patterns,
    8: ut.statistical_test,
    9: ct.linear_complexity_test,
    10: serial.serial_test,
    11: aet.approximate_entropy_test,
    12: cst.cumulative_sums_test,
    13: cst.cumulative_sums_test,
    14: ret.random_excursions_test,
    15: ret.variant_test,
}


def save_to_txt(save, name):
    data_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), "data/" + name)
    with open(data_path, "w") as text_file:
        text_file.write(save)


def mersenne_twister_test(n):
    test = np.random.randint(2, size=n)
    bits = "".join([str(i) for i in test])
    save_to_txt(bits, "mersenne_twister_check.txt")


def main(file_names=None, data=None):
    if file_names:
        raise NotImplemented

    if data is None:
        data = []
        for file in file_names:
            data_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), "data/" + file)
            f = open(data_path)

            data_lst = []
            for line in f:
                data_lst.append(line.strip().rstrip())
            data.append("".join(data_lst))

        results = []
        for item in data:
            result = []
            for c in tqdm(range(len(test_function))):
                result.append([test_type[c], test_function[c](item)])
            results.append(result)
    else:
        results = []
        for c in tqdm(range(len(test_function))):
            results.append([test_type[c], test_function[c](data)])

    return results
