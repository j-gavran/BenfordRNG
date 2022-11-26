import time
from dataclasses import dataclass, field

from RWV.pushshift.time_utils import timestamp_to_utc as to_utc


class Posts:
    """Creates Posts object from pushshift link."""

    def __init__(self, query="", sort="desc", size=25, after=0, before=int(time.time()), subreddit=""):
        """
        Parameters
        ----------
        query: Not supported (see pushshift docs).
        sort: Descending or ascending. Defaults to 'desc'.
        size: Number of objects in API call (max 1000 per call).
        after(int): Unix timestamp.
        before(int): Unix timestamp.
        subreddit: Subreddit, if '' then r/all.

        """
        self.query = query
        self.sort = sort
        self.size = size
        self.after = after
        self.before = before
        self.sub = subreddit
        self.content = "submission"

    def make_url(self):
        url = "https://api.pushshift.io/reddit/search/{}/?q={}&size={}&sort={}&after={}&before={}&subreddit={}".format(
            self.content, self.query, self.size, self.sort, self.after, self.before, self.sub
        )
        return url


class Comments(Posts):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.content = "comment"


@dataclass(order=True, frozen=True)
class Post:
    sort_index: int = field(init=False, repr=False)
    author: str
    created_utc: int
    post_id: str
    num_comments: int
    score: int
    subreddit: str
    title: str
    selftext: str
    permalink: str
    is_post = True

    def __post_init__(self):
        object.__setattr__(self, "sort_index", self.created_utc)

    def __str__(self):
        return f"u/{self.author} posted in r/{self.subreddit} at {to_utc(self.created_utc)} with title:\n{self.body}\nand selftext:\n{self.selftext}"

    def __repr__(self):
        return f"{self.__class__.__name__}(u/{self.author} in r/{self.subreddit} at {to_utc(self.created_utc)})"


@dataclass(order=True, frozen=True)
class Comment:
    sort_index: int = field(init=False, repr=False)
    author: str
    body: str
    created_utc: int
    link_id: str
    parent_id: str
    score: int
    subreddit: str
    permalink: str
    is_post = False

    def __post_init__(self):
        object.__setattr__(self, "sort_index", self.created_utc)

    def __str__(self):
        return f"u/{self.author} commented in r/{self.subreddit} at {to_utc(self.created_utc)} with:\n{self.body}"

    def __repr__(self):
        return f"{self.__class__.__name__}(u/{self.author} in r/{self.subreddit} at {to_utc(self.created_utc)})"


def get_permalink(json):
    if "permalink" in json:
        return json["permalink"]
    else:
        return ""


def make_post(json: dict):
    return Post(
        json["author"],
        json["created_utc"],
        json["id"],
        json["num_comments"],
        json["score"],
        json["subreddit"],
        json["title"],
        json["selftext"],
        get_permalink(json),
    )


def make_comment(json: dict):
    return Comment(
        json["author"],
        json["body"],
        json["created_utc"],
        json["link_id"],
        json["parent_id"],
        json["score"],
        json["subreddit"],
        get_permalink(json),
    )


# post:
# {'all_awardings': [],
#  'allow_live_comments': False,
#  'author': 'Rocky_Roku',
#  'author_flair_css_class': None,
#  'author_flair_richtext': [],
#  'author_flair_text': None,
#  'author_flair_type': 'text',
#  'author_fullname': 't2_cqkopiy2',
#  'author_is_blocked': False,
#  'author_patreon_flair': False,
#  'author_premium': False,
#  'awarders': [],
#  'can_mod_post': False,
#  'content_categories': ['entertainment'],
#  'contest_mode': False,
#  'created_utc': 1627389562,
#  'domain': 'self.anime',
#  'full_link': 'https://www.reddit.com/r/anime/comments/osm1br/how_the_episode_the_ragnarok_connection_made_me/',
#  'gildings': {},
#  'id': 'osm1br',
#  'is_created_from_ads_ui': False,
#  'is_crosspostable': True,
#  'is_meta': False,
#  'is_original_content': False,
#  'is_reddit_media_domain': False,
#  'is_robot_indexable': True,
#  'is_self': True,
#  'is_video': False,
#  'link_flair_background_color': '#7193ff',
#  'link_flair_css_class': 'discussion',
#  'link_flair_richtext': [],
#  'link_flair_template_id': 'eeafce2a-7ef5-11e8-a46a-0e47aad96570',
#  'link_flair_text': 'Discussion',
#  'link_flair_text_color': 'light',
#  'link_flair_type': 'text',
#  'locked': False,
#  'media_only': False,
#  'no_follow': True,
#  'num_comments': 5,
#  'num_crossposts': 0,
#  'over_18': False,
#  'parent_whitelist_status': 'all_ads',
#  'permalink': '/r/anime/comments/osm1br/how_the_episode_the_ragnarok_connection_made_me/',
#  'pinned': False,
#  'pwls': 6,
#  'retrieved_on': 1627389574,
#  'score': 1,
#  'selftext': '',
#  'send_replies': True,
#  'spoiler': True,
#  'stickied': False,
#  'subreddit': 'anime',
#  'subreddit_id': 't5_2qh22',
#  'subreddit_subscribers': 2621185,
#  'subreddit_type': 'public',
#  'thumbnail': 'spoiler',
#  'title': 'How the episode "The Ragnarok Connection" made me fall out of love '
#           'with Code Geass',
#  'total_awards_received': 0,
#  'treatment_tags': [],
#  'upvote_ratio': 1.0,
#  'url': 'https://www.reddit.com/r/anime/comments/osm1br/how_the_episode_the_ragnarok_connection_made_me/',
#  'whitelist_status': 'all_ads',
#  'wls': 6}

# comment:
# {'all_awardings': [],
#  'associated_award': None,
#  'author': 'ha_ck_rm_rk',
#  'author_flair_background_color': None,
#  'author_flair_css_class': None,
#  'author_flair_richtext': [],
#  'author_flair_template_id': None,
#  'author_flair_text': None,
#  'author_flair_text_color': None,
#  'author_flair_type': 'text',
#  'author_fullname': 't2_60vh2iok',
#  'author_patreon_flair': False,
#  'author_premium': False,
#  'awarders': [],
#  'body': "",
#  'collapsed_because_crowd_control': None,
#  'comment_type': None,
#  'created_utc': 1622440789,
#  'gildings': {},
#  'id': 'h01zzht',
#  'is_submitter': False,
#  'link_id': 't3_nml3mm',
#  'locked': False,
#  'no_follow': True,
#  'parent_id': 't1_h01zs6w',
#  'permalink': '/r/anime/comments/nml3mm/casual_discussion_fridays_week_of_may_28_2021/h01zzht/',
#  'retrieved_on': 1622537914,
#  'score': 3,
#  'send_replies': True,
#  'stickied': False,
#  'subreddit': 'anime',
#  'subreddit_id': 't5_2qh22',
#  'top_awarded_type': None,
#  'total_awards_received': 0,
#  'treatment_tags': []}
