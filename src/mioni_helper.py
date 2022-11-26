import os

import pandas as pd


def load_mioni_data():
    data_dir = os.path.join(os.path.abspath(os.path.dirname(__file__)), "mioni_data/")

    dfs = []
    for i in range(3):
        df = pd.read_csv(data_dir + f"TDC_{i + 1}.txt", sep="\t")
        df.columns = ["us", "N"]
        dfs.append(df)

    return dfs
