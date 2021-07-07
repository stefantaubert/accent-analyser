import dataclasses
from collections import Counter, OrderedDict
from copy import deepcopy
from dataclasses import dataclass, field
from difflib import ndiff
from enum import IntEnum
from logging import StrFormatStyle, getLogger
from random import choices
from typing import Dict, Iterable, List, Optional
from typing import OrderedDict as OrderedDictType
from typing import Set, Tuple

import numpy as np
from accent_analyser.core.rule_detectionv2 import WordEntry
from ordered_set import OrderedSet
from pandas import DataFrame
from text_utils import (IPAExtractionSettings, Language, strip_word,
                        symbols_to_lower, text_to_symbols)
from text_utils.language import get_lang_from_str, is_lang_from_str_supported


def get_probabilities(words: List[WordEntry]) -> List[Tuple[str, str, int, int]]:
  tmp = {}
  for word in words:
    k = symbols_to_str_with_space(word.phonemes)
    v = symbols_to_str_with_space(word.phones)
    if k not in tmp:
      tmp[k] = []
    tmp[k].append(v)

  res = []
  for phoneme_str, phones_strs in tmp.items():
    assert len(phones_strs) > 0
    c = Counter(phones_strs)
    if len(c) == 1:
      continue
    for phone_str, count in c.items():
      res.append((
        phoneme_str,
        phone_str,
        count
      ))

  res.sort(key=lambda x: (x[0], -x[2]))

  return res


def probabilities_to_df(probs: List[Tuple[str, str, int]]) -> DataFrame:
  res = DataFrame(
    data=probs,
    columns=["phonemes", "phones", "occurrence"],
  )

  return res


def parse_probabilities_df(df: DataFrame) -> Dict[Tuple[str, ...], List[Tuple[Tuple[str, ...], int]]]:
  res: Dict[Tuple[str, ...], List[Tuple[Tuple[str, ...], int]]] = dict()
  for _, row in df.iterrows():
    phonemes = tuple(str(row["phonemes"]).split(" "))
    phones = tuple(str(row["phones"]).split(" "))
    prob = int(row["occurrence"])
    if phonemes not in res:
      res[phonemes] = []
    res[phonemes].append((phones, prob))
  return res


def check_probabilities_are_valid(d: Dict[Tuple[str, ...], List[Tuple[Tuple[str, ...], int]]]) -> bool:
  logger = getLogger(__name__)
  is_valid = True
  for k, v in d.items():
    replace_with, replace_with_prob = list(zip(*v))
    set_replace_with = set(replace_with)
    k_str = " ".join(k)
    any_prob_is_zero = any(x == 0 for x in replace_with_prob)
    if any_prob_is_zero:
      is_valid = False
      logger.error(
        f"A least one probability was set to zero {k_str}!")
    if len(replace_with) != len(set_replace_with):
      is_valid = False
      logger.error(f"Some phones are defined multiple times inside phoneme {k_str}!")
  return is_valid


def replace_with_prob(symbols: Tuple[str, ...], d: Dict[Tuple[str, ...], List[Tuple[Tuple[str, ...], int]]]) -> Tuple[str, ...]:
  assert symbols in d
  replace_with, replace_with_prob = list(zip(*d[symbols]))
  res = choices(replace_with, weights=replace_with_prob, k=1)[0]
  # res_idx = np.random.choice(len(replace_with), 1, p=replace_with_prob)[0]
  # res = replace_with[res_idx]
  return res


def symbols_to_str_with_space(symbols: List[str]) -> str:
  return " ".join(symbols)
