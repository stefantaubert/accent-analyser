from typing import List
from typing import OrderedDict as OrderedDictType
from typing import Tuple

from accent_analyser.core.rule_detection import (PhonemeOccurrences,
                                                 PhoneOccurrences, WordEntry,
                                                 WordRules, rules_to_str)
from pandas import DataFrame

WordStatsEntry = Tuple[str, str, str, str, int, int, str]


def get_word_stats(word_rules: OrderedDictType[WordEntry, WordRules], phone_occurrences: PhoneOccurrences, phoneme_occurrences: PhonemeOccurrences) -> List[WordStatsEntry]:
  res: List[WordStatsEntry] = []
  phoneme_ids = {k: i for i, k in enumerate(sorted(phoneme_occurrences.keys()))}
  for word, rule in word_rules.items():
    phoneme_id = phoneme_ids[(word.graphemes, word.phonemes)]
    phoneme_id_one_based = phoneme_id + 1
    total_occ = phoneme_occurrences[(word.graphemes, word.phonemes)]
    phone_occ = phone_occurrences[word]
    rules_str = rules_to_str(rule)
    occurrence_percent = phone_occ / total_occ * 100

    res.append((
      phoneme_id_one_based,
      word.graphemes_str,
      word.phonemes_str,
      word.phones_str,
      rules_str,
      phone_occ,
      total_occ,
      f"{occurrence_percent:.2f}",
    ))

  sort_word_stats(res)
  # res.sort(key=lambda x: (x[0], x[4] - x[3], x[1].phones_str))
  return res


def sort_word_stats(resulting_csv_data: List[WordStatsEntry]):
  ''' Sorts: Word ASC, Occurrences DESC, Phones ASC'''
  resulting_csv_data.sort(key=lambda x: (x[0], x[6] - x[5], x[3]))


def word_stats_to_df(word_stats: List[WordStatsEntry]) -> DataFrame:
  res = DataFrame(
    data=word_stats,
    columns=["Nr", "English", "Phonemes", "Phones", "Rules",
             "Occurrences", "Occurrences Total", "Occurrences (%)"],
  )

  return res
