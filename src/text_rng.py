import logging
import pickle

import numpy as np
from tqdm import tqdm

from benford_helper_functions import binary_tree_walk, get_bitstring, str_to_bits
from NIST_tests import RNG_test
from stat_tests import chi2_test, ks_test


def make_bit_chunk(bits, n):
    m = len(bits) // n
    bits_chunked = [bits[i * m : (i + 1) * m] for i in range(n)]
    return bits_chunked


def make_bit_chunks(bits, n=32):
    end_parts, elements = n, len(bits) // n
    logging.debug(f"end parts: {end_parts} with {elements} elements")
    bits_chunked = make_bit_chunk(bits, n)
    return bits_chunked, end_parts, elements


def make_bitstring_from_chunks(bits, num_bits=None, **kwargs):
    bits_chunked, n_chunks, elements = make_bit_chunks(bits, **kwargs)

    bitstring = ""
    for i in range(elements):
        for j in range(n_chunks):
            b = bits_chunked[j][i]
            bitstring += b
            if num_bits:
                if len(bitstring) > num_bits:
                    return bitstring

    return bitstring


def bit_mixer(st, n_mixes=None, chunks=None):
    starting_st = st

    if chunks is None:
        n = int(np.sqrt(len(st))) - 1
        print(f"using {n} chunks")
    else:
        n = chunks

    if n_mixes is None:
        n_mixes = n

    for i in range(n_mixes):
        st = make_bitstring_from_chunks(st, n=n)
        if st == starting_st:
            print("sequence repeated! returnig last good combination!")
            return old_st
        old_st = st

    return st


def make_float_chunks(fl, n):
    m = len(fl) // n
    bits_chunked = [fl[i * m : (i + 1) * m] for i in range(n)]
    return bits_chunked


def make_floatarr_from_chunks(fl, num_fl=None, n=2):  # n -> chunks
    floats_chunked = make_float_chunks(fl, n)
    elements = len(fl) // n

    floatarr = []
    for i in range(elements):
        for j in range(n):
            f = floats_chunked[j][i]
            floatarr.append(f)

            if num_fl and len(floatarr) > num_fl:
                return floatarr

    return np.array(floatarr)


def float_mixer(fl, n_mixes, **kwargs):
    for m in tqdm(range(n_mixes)):
        fl = make_floatarr_from_chunks(fl, **kwargs)
    return np.array(fl)


def utf8_bits(text, utf8_bit_pos=-1, top_words=None, remove_spaces=True):
    full_text = "".join(text)
    spaces_bits = str_to_bits(full_text, to_replace=top_words, remove_spaces=remove_spaces)

    list_bits = list(spaces_bits.split(" "))

    bits = ""
    for b in list_bits:
        try:
            bits += b[utf8_bit_pos]
        except Exception as e:
            print(e, b)
            pass

    return bits


def make_ints_with_n_bits(bits, n):
    m = len(bits) // n

    ints = []
    for i in range(m):
        take = bits[i * n : (i + 1) * n]
        make_int = int(take, 2)
        if make_int != 0:
            ints.append(make_int)

    return np.array(ints)


def reshape_and_truncate(arr, shape):
    desired_size_factor = np.prod([n for n in shape if n != -1])
    if -1 in shape:
        desired_size = arr.size // desired_size_factor * desired_size_factor
    else:
        desired_size = desired_size_factor
    return arr.flat[:desired_size].reshape(shape)


def text_lognormal_dist(bits, n, d, div=1):
    """
    bits: str
        Sequence of bits
    n: int
        Number of bits to take together in bits sequence
    d: int
        Number of multiplications
    """
    ints = make_ints_with_n_bits(bits, n=n)
    ints_mat = reshape_and_truncate(ints, (len(ints) // d, d))
    ints_prod = np.prod(ints_mat / div, axis=1)
    return ints_prod


class TextRng:
    def __init__(self, text, utf8_kwargs=None, mixing_kwargs=None, lognormal_kwargs=None, bit_generation="walk"):
        if type(text) == list or type(text) == np.ndarray:
            text = "".join(text)
        self.text = text

        if utf8_kwargs is None:
            utf8_kwargs = {"utf8_bit_pos": -1, "top_words": None, "remove_spaces": True}

        if mixing_kwargs is None:
            mixing_kwargs = {"n_mixes": 1, "chunks": 16}

        if lognormal_kwargs is None:
            lognormal_kwargs = {"n": 8, "d": 6, "div": 1e6}

        self.utf8_kwargs = utf8_kwargs
        self.mixing_kwargs = mixing_kwargs
        self.lognormal_kwargs = lognormal_kwargs
        self.bit_generation = bit_generation
        self.test_results, self.rng_test_results = None, None

    def run(self):
        bits = utf8_bits(self.text, **self.utf8_kwargs)

        mixed_bits = bit_mixer(bits, **self.mixing_kwargs)

        prod = text_lognormal_dist(mixed_bits, **self.lognormal_kwargs)

        u = np.log10(prod) % 1
        chi2, ks = chi2_test(u), ks_test(u)
        self.test_results = [chi2, ks]

        if self.bit_generation == "walk":
            rng_bits = binary_tree_walk(u).astype(str)
        elif self.bit_generation == "bitstring":
            rng_bits = get_bitstring(u)
        else:
            raise NameError

        rng_bits = "".join(rng_bits)

        return rng_bits

    def test(self, max_bits=None):
        bits = self.run(max_bits)

        if max_bits:
            bits = bits[:max_bits]

        rng_test_results = RNG_test(bits)
        self.rng_test_results = rng_test_results

        return rng_test_results

    def pickle(self, f_name):
        pickle.dump([self.test_results, self.rng_test_results], open(f"{f_name}.p", "wb"))
