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
from ordered_set import OrderedSet
from pandas import DataFrame
from text_utils import (IPAExtractionSettings, Language, strip_word,
                        symbols_to_lower, text_to_symbols)
from text_utils.language import get_lang_from_str, is_lang_from_str_supported

from accent_analyser.core.rule_detectionv2 import PhoneOccurrences, PhonemeOccurrences, WordEntry, WordRules, rules_to_str


WordStatsEntry = Tuple[int, WordEntry, WordRules, int, int]


def get_word_stats(word_rules: OrderedDictType[WordEntry, WordRules], phone_occurrences: PhoneOccurrences, phoneme_occurrences: PhonemeOccurrences) -> List[WordStatsEntry]:
  res: List[WordStatsEntry] = []
  for i, (word, rule) in enumerate(word_rules.items()):
    total_occ = phoneme_occurrences[(word.graphemes, word.phonemes)]
    phone_occ = phone_occurrences[word]
    res.append((
      i,
      word,
      rule,
      phone_occ,
      total_occ,
    ))
  return res


def word_stats_to_df(word_stats: List[WordStatsEntry]) -> DataFrame:
  resulting_csv_data = []
  for i, word, rules, count, total_count in word_stats:
    rules_str = rules_to_str(rules)
    resulting_csv_data.append((
      i + 1,
      word.graphemes_str,
      word.phonemes_str,
      word.phones_str,
      rules_str,
      count,
      total_count,
      f"{count/total_count*100:.2f}",
    ))

  sort_word_stats_df(resulting_csv_data)

  res = DataFrame(
    data=resulting_csv_data,
    columns=["Nr", "English", "Phonemes", "Phones", "Rules",
             "Occurrences", "Occurrences Total", "Occurrences (%)"],
  )

  return res


def sort_word_stats_df(resulting_csv_data: List[Tuple[str, str, str, str, int, int, str]]):
  ''' Sorts: Word ASC, Occurrences DESC, Phones ASC'''
  resulting_csv_data.sort(key=lambda x: (x[0], x[6] - x[5], x[3]))

