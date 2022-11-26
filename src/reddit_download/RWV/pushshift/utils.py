import glob
import itertools
import logging
import multiprocessing
import os
import random
import re
import time
from concurrent.futures import ProcessPoolExecutor
from datetime import datetime

import numpy as np
import pandas as pd
from RWV.pushshift.get_data_threading import GetContent
from RWV.pushshift.load_data import Content
from RWV.pushshift.time_utils import seconds_in_day, timestamp_to_utc


def get_filenames(path=None, full_paths=False):
    if path is None:
        path = os.path.abspath("") + "/RWV/data/reddit_data"
    else:
        path = path + "/RWV/data/reddit_data"

    # file_lst = os.listdir(path)
    _full_paths = glob.glob(path + "/**/*.json.gz", recursive=True)

    if full_paths:
        file_lst = _full_paths
    else:
        file_lst = [f[len(path) + 1 :] for f in _full_paths]

    saved_reddit = []
    for file in file_lst:
        if file != ".gitignore":
            saved_reddit.append(file)

    return saved_reddit


def delete_empty_json_files(path=None):
    files = get_filenames(path)

    for file in files:
        f_data = Content(file).load_content_from_file()
        if len(f_data.data) == 0:
            os.remove(get_file_path(file))
            logging.info(f"deleted {file}")


def resume_downloads(end_at=None, path=None, delete_empty=True):
    logging.info("resuming downloads...")
    if delete_empty:
        delete_empty_json_files(path)
    files = get_filenames(path)

    stopped_at = {}
    started_at = {}
    for f in files:
        sub = re.findall(".*?(?=_\d)", f)[0]
        n = int(re.findall("_\d*_", f)[0][1:-1])
        content = re.findall("\d_(.*)", f)[0].split(".")[0][:-1]

        if sub not in stopped_at:
            stopped_at[sub] = [n, f, content]
        elif stopped_at[sub][0] < n:
            stopped_at[sub] = [n, f, content]

        if sub not in started_at:
            started_at[sub] = [n, f, content]
        elif started_at[sub][0] > n:
            started_at[sub] = [n, f, content]

    if end_at is None:
        end_at = max([i[0] for i in stopped_at.values()])

    resume_dct = {}
    for (sub, stopped), (_, started) in zip(stopped_at.items(), started_at.items()):
        if stopped[0] != end_at:
            fstart, fstop = started[1], stopped[1]
            c_objstart, c_objstop = Content(fstart), Content(fstop)

            if stopped[2] == "post" and started[2] == "post":
                content_start, content_stop = c_objstart.load_posts(), c_objstop.load_posts()
            else:
                content_start, content_stop = c_objstart.load_comments(), c_objstop.load_comments()

            if stopped[0] != started[0]:
                srt_start, srt_stop = sorted(content_start), sorted(content_stop)
                resume_dct[sub] = [(srt_start[0].created_utc, srt_stop[-1].created_utc), stopped[2]]
            else:
                resume_dct[sub] = [True, stopped[2]]
        else:
            resume_dct[sub] = [False, stopped[2]]

    return resume_dct, started_at, stopped_at


def get_content(after, before, subreddit, save_file_name, content, thread_num=4, max_per_sec=1):
    cont = GetContent(
        after=after,
        before=before,
        subreddit=subreddit,
        content=content,
        thread_num=thread_num,
        max_per_sec=max_per_sec,
    )
    cont.get_content()
    cont.save_content(save_file_name)
    return cont


def get_data_by_days(subreddit, ts, content, now_time, delta_t, resumed=None, **kwargs):

    t2 = now_time
    api_calls, cont_count = 0, 0

    for t in ts:
        t1 = now_time - (t + 1) * delta_t

        print("getting {}s from {} to {}".format(content, timestamp_to_utc(t1), timestamp_to_utc(t2)))

        if resumed:
            day_str = f"{t + resumed}" if len(str(t + resumed)) > 1 else f"0{t + resumed}"
        else:
            day_str = f"{t}" if len(str(t)) > 1 else f"0{t}"

        cont = get_content(t1, t2, subreddit, "{}_{}_{}s".format(subreddit, day_str, content), content, **kwargs)
        api_calls += cont.api_calls
        cont_count += len(cont.data)
        t2 = t1

        logging.info(f"collected {cont_count} {cont.content}s with {api_calls} API calls\n")

    return api_calls


def get_subreddit_data_by_days(subs, t, c, start_time=None, delta_t=86400, res_kwargs=None, utc_offset=7200, **kwargs):
    """Download posts or comments from given subreddits.

    Parameters
    ----------
    subs : list
        List of subreddits
    t : int
        Numer of time iterations
    c : str
        Content: post or comment
    start_time : int, optional
        Starting timestamp, by default int(time.time())
    delta_t : int, optional
        Move this delta in time each iteration given by t, by default 86400
    resume_path : str, optional
        File path to saved data for resuming download, by default None
    utc_offset : int, optional
        Timezone offset, by default 7200
    """
    if res_kwargs is None:
        res_kwargs = {}

    resume_dct, _, _ = resume_downloads(**res_kwargs)
    resumed = None

    if start_time is None:
        start_time = int(time.time())

    for sub in subs:
        now_time = start_time - seconds_in_day(datetime.now()) + utc_offset

        ts = np.arange(0, t, 1)

        if sub not in resume_dct:
            correct_sub = None
        else:
            correct_sub = c == resume_dct[sub][1]

        if sub not in resume_dct:
            pass
        elif resume_dct[sub][0] is True:
            pass
        elif resume_dct[sub][0] is False and correct_sub:
            continue
        elif correct_sub:
            t_start, t_stop = resume_dct[sub][0][0], resume_dct[sub][0][1]
            dt = abs(t_start - t_stop)
            total = t * delta_t - dt
            new_t = int(total / delta_t)

            ts = np.arange(0, new_t, 1)

            now_time = t_stop
            resumed = t - new_t + 1

            print("resume at {}".format(timestamp_to_utc(now_time)))

        print("data from {} for {} days\n".format(sub, t))
        get_data_by_days(sub, ts, c, now_time=now_time, delta_t=delta_t, resumed=resumed, **kwargs)

    logging.info("DONE")


def _build_df(content_type, file_names):
    if content_type == "post":
        fields = [
            "author",
            "created_utc",
            "post_id",
            "num_comments",
            "score",
            "subreddit",
            "title",
            "selftext",
            "permalink",
        ]
    elif content_type == "comment":
        fields = [
            "author",
            "body",
            "created_utc",
            "link_id",
            "parent_id",
            "score",
            "subreddit",
            "permalink",
        ]
    else:
        raise ValueError

    df_main_dct = {f: [] for f in fields}

    for file_name in file_names:
        c_obj = Content(file_name)

        if content_type == "comment":
            iter_ = c_obj.load_comments()
        else:
            iter_ = c_obj.load_posts()

        for content in iter_:
            df_dct = {f: getattr(content, f) for f in fields}

            for k, v in df_dct.items():
                df_main_dct[k].append(v)

    return df_main_dct


def build_df(content_type, file_names=None, file_path=None, workers=None, subreddits=None, return_dct=False):
    if file_names is None:
        file_names = get_filenames(path=file_path if file_path else None)

    if subreddits is not None:
        _file_names = []
        for f in file_names:
            sub = re.findall(".*?(?=_\d)", f)[0]
            if sub in subreddits:
                _file_names.append(f)
        file_names = _file_names

    random.shuffle(file_names)

    if workers is None:
        workers = multiprocessing.cpu_count() // 2
    elif workers == 1:
        return pd.DataFrame(_build_df(content_type, file_names))
    else:
        logging.info(f"using {workers} workers")

    split_file_names = []
    split = len(file_names) // workers

    for i in range(workers + 1):
        split_file_names.append(file_names[i * split : (i + 1) * split])

    with ProcessPoolExecutor(max_workers=workers) as executor:
        futures = []
        for f in split_file_names:
            future = executor.submit(_build_df, content_type, f)
            futures.append(future)

    results = [future.result() for future in futures]
    df_dct = {k: [] for k in results[0].keys()}

    for dct in results:
        for k, v in dct.items():
            df_dct[k].append(v)

    flatten = itertools.chain.from_iterable

    for k, v in df_dct.items():
        df_dct[k] = list(flatten(v))

    if return_dct:
        return df_dct
    else:
        return pd.DataFrame(df_dct)


def apply_df_time_transforms(df):
    df["datetime"] = df["created_utc"].apply(datetime.fromtimestamp)
    df = df.rename(columns={"created_utc": "timestamp"})
    df["time_in_day"] = df["datetime"].apply(seconds_in_day)
    df["weekday"] = df["datetime"].apply(datetime.weekday)
    df["date"] = df["datetime"].apply(lambda x: str(datetime.date(x)))
    return df


def get_file_path(file):
    return os.path.join(os.path.abspath(os.path.dirname(__file__)), "../data/reddit_data/" + file)


def rename_to_offset(off, files):
    for f in files:
        sp = f.split("_")
        sub, n_file, ext = sp[0], int(sp[1]), sp[2]

        if n_file > off:
            n_new = n_file - off + 1
            os.rename(get_file_path(f), get_file_path(f"{sub}_{n_new}_{ext}"))
