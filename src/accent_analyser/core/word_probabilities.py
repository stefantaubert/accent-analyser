from logging import getLogger
from random import choices
from typing import Dict, List, Tuple

from accent_analyser.core.rule_detection import (PhonemeOccurrences,
                                                 PhoneOccurrences)
from pandas import DataFrame

Symbols = Tuple[str, ...]
ProbabilitiesDict = Dict[Symbols, List[Tuple[Symbols, int]]]

_ProbabilityEntry = Tuple[str, str, int]

_PHONEMES_COL_NAME = "Phonemes"
_PHONES_COL_NAME = "Phones"
_OCCURRENCE_COL_NAME = "Occurrence"


def get_probabilities(phone_occurrences: PhoneOccurrences, phoneme_occurrences: PhonemeOccurrences) -> List[_ProbabilityEntry]:
  probabilities = []
  for word, word_occurrences in phone_occurrences.items():
    word_is_always_the_same = phoneme_occurrences[(
      word.graphemes, word.phonemes)] == word_occurrences
    if word_is_always_the_same:
      continue
    probabilities.append((
      symbols_to_str_with_space(word.phonemes),
      symbols_to_str_with_space(word.phones),
      word_occurrences,
    ))

  sort_probabilities(probabilities)

  return probabilities


def sort_probabilities(probabilities: List[_ProbabilityEntry]) -> None:
  probabilities.sort(key=lambda x: (x[0], -x[2], x[1]))


def probabilities_to_df(probs: List[_ProbabilityEntry]) -> DataFrame:
  res = DataFrame(
    data=probs,
    columns=[_PHONEMES_COL_NAME, _PHONES_COL_NAME, _OCCURRENCE_COL_NAME],
  )

  return res


def parse_probabilities_df(df: DataFrame) -> ProbabilitiesDict:
  res: ProbabilitiesDict = dict()
  for _, row in df.iterrows():
    phonemes = symbols_from_str_with_space(row[_PHONEMES_COL_NAME])
    phones = symbols_from_str_with_space(row[_PHONES_COL_NAME])
    prob = int(row[_OCCURRENCE_COL_NAME])
    if phonemes not in res:
      res[phonemes] = []
    res[phonemes].append((phones, prob))
  return res


def check_probabilities_are_valid(probabilities: ProbabilitiesDict) -> bool:
  logger = getLogger(__name__)
  is_valid = True
  for k, v in probabilities.items():
    replace_with, replace_with_prob = list(zip(*v))
    set_replace_with = set(replace_with)
    k_str = symbols_to_str_with_space(k)
    any_prob_is_zero = any(x == 0 for x in replace_with_prob)
    if any_prob_is_zero:
      is_valid = False
      logger.error(
        f"A least one probability was set to zero {k_str}!")
    if len(replace_with) != len(set_replace_with):
      is_valid = False
      logger.error(f"Some phones are defined multiple times inside phoneme {k_str}!")
  return is_valid


def replace_with_prob(symbols: Symbols, d: ProbabilitiesDict) -> Symbols:
  assert symbols in d
  replace_with, replace_with_prob = list(zip(*d[symbols]))
  res = choices(replace_with, weights=replace_with_prob, k=1)[0]
  return res


def symbols_from_str_with_space(symbols: str) -> Symbols:
  return tuple(symbols.split(" "))


def symbols_to_str_with_space(symbols: Symbols) -> str:
  return " ".join(symbols)
