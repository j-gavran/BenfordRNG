import logging

from RWV.pushshift.utils import get_subreddit_data_by_days


def main():
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)

    subreddits = [
        "MachineLearning",
        "tea",
        "math",
        "askscience",
        "linux",
        "Coffee",
        "Physics",
        "space",
        "Amd",
        "nvidia",
        "programming",
        "Python",
        "cpp",
        "anime",
    ]

    get_subreddit_data_by_days(
        subreddits, 64, "comment", max_per_sec=1, thread_num=4, res_kwargs={"delete_empty": True}
    )
    get_subreddit_data_by_days(subreddits, 64, "post", max_per_sec=1, thread_num=4, res_kwargs={"delete_empty": True})


if __name__ == "__main__":
    main()
