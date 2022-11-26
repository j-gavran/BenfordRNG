import os
import sys
from collections import OrderedDict

import numpy as np
import pandas as pd

sys.path.insert(0, os.getcwd() + "/randomness_testsuite")

from randomness_testsuite.tests_main import main


def RNG_test(bits, short_df=False):
    """A hacked together wrapper for https://github.com/stevenang/randomness_testsuite"""
    res = main(data=bits)

    names = []
    for r in res:
        names.append(r[0][4:])

    p_values = []

    for i, r in enumerate(res[:-3]):
        t = r[1]
        for item in t:
            if type(item) == np.float64 or type(item) == float:
                p_values.append(item)

        if i == 9:
            p_values.append((res[10][1][0][0] + res[10][1][1][0]) / 2)  # TODO: do something with multiple returns

    r1, r2 = [], []

    for i in res[-1][1]:
        r1.append(i[3])

    for i in res[-2][1]:
        r2.append(i[3])

    r1, r2 = np.array(r1), np.array(r2)

    p_values.append(r2[0])  # TODO: same as above
    p_values.append(r1[0])  #

    names.pop(13)  # two similar tests, get rid of one

    tests_dct = OrderedDict([(k, v) for k, v in zip(names, p_values)])

    df = pd.DataFrame([tests_dct]).T.reset_index()
    df.columns = ["test", "p"]
    df["p"][df["p"] < 0] = np.nan
    df["p"] = df["p"].apply(lambda x: f"{x:.2f}")

    if short_df:
        del df["test"]
        df = df.T

    return df


if __name__ == "__main__":
    bits = np.random.randint(2, size=10000).astype(str)
    bits = "".join(bits)

    df = RNG_test(bits)
    print(df)
