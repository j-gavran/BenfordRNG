import gzip
import json
import logging
import math
import os
import threading
import time

import requests
from RWV.pushshift.classes import Comments, Posts
from RWV.pushshift.time_utils import timestamp_to_utc as to_utc


class ThreadRateLimiter:
    def __init__(self, thread_name, max_per_sec, thread_num, offset):
        """Rate limiter for each active thread.

        Parameters
        ----------
        thread_name : str
            Name of thread, usually thread_0, thread_1, ...
        max_per_sec : float
            Calls to API per second
        thread_num : int
            Number of threads
        offset : float
            Starting time offset, usually 1 / thread_num
        """
        thread_max_per_sec = max_per_sec / thread_num

        self.init_time = time.time()
        self.thread_name, self.thread_num = thread_name, thread_num

        self.rate, self.per = thread_max_per_sec, 1 / thread_max_per_sec
        self.last_check, self.past_last_check = time.time() + offset, time.time() + offset

        self.hits = 0
        self.calls, self.past_calls = 0, 0

    def __call__(self):
        current = time.time()
        time_passed = current - self.last_check
        self.last_check = current

        self.calls += 1

        if time_passed < self.per:
            sleep = self.per - time_passed
            self.last_check += sleep
            return sleep
        else:
            return 0

    def __str__(self):
        dt, dcalls = self.last_check - self.past_last_check, self.calls - self.past_calls
        ret = f"thread {self.thread_name}: {self.calls} API calls, dt: {dt:.3f}, current rate: {(dcalls / dt) * self.thread_num:.3f}"
        self.past_last_check, self.past_calls = self.last_check, self.calls
        return ret


class GetContent:
    def __init__(self, after, subreddit, content, before=time.time(), size=1000, thread_num=1, max_per_sec=1):
        """Threading class for pushshift API.

        Parameters
        ----------
        after : int
            Timestamp
        subreddit : str
            Name of subreddit
        content : str
            Comment or post
        before : int, optional
            Timestamp, by default time.time()
        size : int, optional
            Number of returned objects of type content, by default 1000 (new is 100)
        thread_num : int, optional
            Number of thread, by default 1
        max_per_sec : int, optional
            Calls to API per second, by default 1

        """
        self.start_time = time.time()
        self.after, self.before = after, before
        self.content = content
        self.subreddit = subreddit
        self.size = size

        self.thread_num = thread_num
        self.max_per_sec = max_per_sec

        self.data = []
        self.s = requests.Session()
        self.lock = threading.Lock()
        self.api_calls = 0

    def get_intervals(self):
        """Make time intervals."""

        t1 = int(self.after)
        t2 = int(self.before)
        delta_t = int((t2 - t1) / self.thread_num)

        intervals = []
        for i in range(self.thread_num):
            intervals.append([t1 + delta_t * i, t1 + delta_t * (i + 1) - 1])

        return intervals

    def get_content(self):
        """Thread initialization function."""

        intervals = self.get_intervals()
        threads_lst = []

        start_offset = 1 / self.thread_num

        thread_limiters = [
            ThreadRateLimiter(i, self.max_per_sec, self.thread_num, start_offset) for i in range(self.thread_num)
        ]

        for i in range(self.thread_num):
            if self.content == "post":
                my_data = Posts(
                    after=intervals[i][0],
                    before=intervals[i][1],
                    size=self.size,
                    subreddit=self.subreddit,
                )
            elif self.content == "comment":
                my_data = Comments(
                    after=intervals[i][0],
                    before=intervals[i][1],
                    size=self.size,
                    subreddit=self.subreddit,
                )
            else:
                raise NameError

            t = threading.Thread(
                target=self.thread_content,
                name="thread_{}".format(i),
                args=(my_data, f"thread_{i}", thread_limiters[i]),
            )
            time.sleep(start_offset)
            t.start()
            threads_lst.append(t)
            logging.info("{} has started\n".format(t.name))

        for t in threads_lst:
            t.join()

        logging.info("\ntotal time: {:.2f} s\n".format(time.time() - self.start_time))
        logging.info("total api calls: {}\n".format(self.api_calls))
        logging.info("number of posts/comments collected: {}\n".format(len(self.data)))
        time.sleep(1)

        return self

    def thread_content(self, iter_content, thread_name, limiter):
        """Main function for threading.

        Parameters
        ----------
        iter_content: class
            Helper class. Remembers after, before and has make_url method
        thread_name: str
            Name of thread running this method
        limiter: class
            ThreadRateLimiter object

        Returns
        -------
        None when done.

        """
        while True:
            logging.info(f"\n{thread_name} collecting: {to_utc(iter_content.after)} to {to_utc(iter_content.before)}")

            my_url = iter_content.make_url()
            data_ = self.get_from_pushshift(my_url, thread_name, limiter)

            logging.debug(f"\npost info: {to_utc(iter_content.after)} to {to_utc(iter_content.before)}\n")

            if data_:
                with self.lock:
                    self.data += data_
                    self.api_calls += 1

                iter_content.before = data_[-1]["created_utc"]

            else:
                break

        logging.info("\n{} done\n".format(thread_name))

        return None

    def _get_from(self, url, thread_name, timeout=10):
        try:
            get_from = self.s.get(url, timeout=timeout)
            status_code = get_from.status_code
        except Exception as e:
            logging.error(f"Exception in {thread_name}; initiating exp backoff")
            logging.debug(e)
            status_code, get_from = 0, None

        return get_from, status_code

    def get_from_pushshift(self, url, thread_name, limiter):
        """Pulls data from pushshift API."""

        with self.lock:
            sleep = limiter()

        if sleep > 0:
            logging.debug("\n{} was over limit; sleeping for {:.3f} s\n".format(thread_name, sleep))
            time.sleep(sleep)

        get_from, status_code = self._get_from(url, thread_name)

        logging.debug(f"\n{str(limiter)}")

        while status_code != 200:
            with self.lock:
                limiter.hits += 1
                limiter.calls += 1
                sleep = math.exp(limiter.hits)
                limiter.last_check = time.time() + sleep

            logging.warning(
                "\nsleeping {} for {:.3f} due to {}\n".format(
                    thread_name, sleep, "error" if status_code == 0 else "requests per sec limit reached"
                )
            )
            time.sleep(sleep)
            logging.debug(f"\n{str(limiter)}")

            get_from, status_code = self._get_from(url, thread_name)

        with self.lock:
            limiter.hits = 0

        ps_data = json.loads(get_from.text)
        if ps_data:
            return ps_data["data"]
        else:
            return None

    def save_content(self, file_name):
        """Saves data to file_name.json.gz."""

        logging.info("\nsaving to file...\n")

        json_str = json.dumps(self.data)
        json_bytes = json_str.encode("utf-8")

        file_name += ".json.gz"

        file_name_ = os.path.join(os.path.abspath(os.path.dirname(__file__)), "../data/reddit_data/" + file_name)
        with gzip.GzipFile(file_name_, "w+") as f:
            f.write(json_bytes)

        logging.info("\ncreated: {}\n".format(file_name))

        return True
