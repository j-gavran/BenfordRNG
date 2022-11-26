import os
import sys

sys.path.insert(0, os.getcwd() + "/reddit_download")

import gzip
import json
import re
from io import StringIO

from tqdm import tqdm

from reddit_download.RWV.pushshift.utils import get_filenames


def load_content_from_file(file_name):
    with gzip.GzipFile(file_name) as f:
        json_bytes = f.read()

    json_str = json_bytes.decode("utf-8")
    data = json.loads(json_str)
    return data


def remove_keys(list_of_dct, keep):
    for dct in list_of_dct:
        dct_loop = dct.copy()
        for k in dct_loop.keys():
            if k not in keep:
                dct.pop(k, None)
    return list_of_dct


def build_df_fast(content_type, pd=None, file_names=None, file_path=None, subreddits=None, keep_keys=None):
    # if pd is None:
    #     import pandas as pd

    if file_names is None:
        file_names = get_filenames(path=file_path if file_path else None, full_paths=True)

    _file_names = []
    for f in file_names:
        content = re.findall("\d_(.*)", f)[0].split(".")[0][:-1]
        if content == content_type:
            _file_names.append(f)
    file_names = _file_names

    if subreddits is not None:
        _file_names = []
        for f in file_names:
            sub = re.findall(".*?(?=_\d)", f)[0]
            sub = sub.rsplit("/", 1)[-1]
            if sub in subreddits:
                _file_names.append(f)
        file_names = _file_names

    if keep_keys is None:
        keep_keys = [
            "author",
            "body",
            "created_utc",
            "link_id",
            "permalink",
            "score",
            "subreddit",
            "id",
            "parent_id",
            "selftext",
            "title",
            "num_comments",
        ]

    lst = []
    for filename in tqdm(file_names):
        data = load_content_from_file(filename)
        data = remove_keys(data, keep_keys)
        df = pd.DataFrame.from_dict(data)
        lst.append(df)

    frame = pd.concat(lst, axis=0, ignore_index=True)
    return frame


def build_df(workers, *args, **kwargs):
    os.environ["MODIN_ENGINE"] = "ray"
    os.environ["MODIN_CPUS"] = str(workers)

    import ray

    ray.init(num_cpus=workers)

    import modin.pandas as pd

    # from modin.config import ProgressBar
    # from tqdm import tqdm
    # ProgressBar.enable()

    df = build_df_fast(*args, pd=pd, **kwargs)
    return df
