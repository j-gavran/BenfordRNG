import operator
import re

from nltk import sent_tokenize


def remove_punctuation(sent):
    sent_nolink = re.sub(r"(?:(?:https?|ftp):\/\/)?[\w/\-?=%.]+\.[\w/\-?=%.]+", "link", sent)
    punct = r'!"#$%&\'()*+,-./:;<=>?@[\\]^_`{|}~' + "’`”“"
    text_nopunct = "".join(char for char in sent_nolink if char not in punct)
    return text_nopunct


def replace_numbers(sent):
    text_nonum = re.sub(r"[0-9]+", "number", sent)
    return text_nonum


def word_by_word(sent):
    tokens = re.split(r"\W+", sent[0])
    tokens_no_empty = [word.lower() for word in tokens if word != ""]
    return tokens_no_empty


def word2vec_input(content, to_sent=False):
    """Prepares content for word2vec.

    Parameters
    ----------
    content: list of post/comment objects
        post.title: str, comment.body: str

    Notes
    -----
    sent_tokenize():  splits into sentences and replaces all links with "link",
    a: replaces numbers with "number", removes punctuation, replaces /n,
    b: lowers,
    c: splits sentence into words

    Returns
    -------
    Sentences word by word in list: [[w1, w2, ...], [w1, w2, ...], ...]
                                        sent1          sent2

    """
    text_in_sent = []

    for obj in content:

        if obj.is_post:
            tokenizer = obj.title
        else:
            tokenizer = obj.body

        for sent in sent_tokenize(tokenizer):
            # a = [replace_numbers(remove_punctuation(sent)).replace('\n', ' ')]
            # b = [i.lower() for i in a]
            # c = word_by_word(b)
            # text_in_sent.append(c)
            if to_sent:
                text_in_sent.append(sent.replace("\n", " "))
            else:
                text_in_sent.append(
                    word_by_word([i.lower() for i in [replace_numbers(remove_punctuation(sent)).replace("\n", " ")]])
                )

    return text_in_sent


def doc2vec_input(content):
    w2v_input = word2vec_input(content)

    doc = []
    for sent in w2v_input:
        doc += sent

    return doc


def count_words(tokenized_lst, sort=None):
    word_count = {}

    for word_lst in tokenized_lst:
        for word in word_lst:
            if word in word_count:
                word_count[word] += 1
            else:
                word_count[word] = 0

    if sort:
        return sorted(word_count.items(), key=operator.itemgetter(1))
    else:
        return word_count
