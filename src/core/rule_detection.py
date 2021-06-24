
from dataclasses import dataclass
from difflib import ndiff
from enum import IntEnum
from logging import getLogger
from typing import List, Optional

from ordered_set import OrderedSet
from pandas import DataFrame
from text_utils import IPAExtractionSettings, Language, text_to_symbols
from text_utils.language import get_lang_from_str, is_lang_from_str_supported


class RuleType(IntEnum):
  OMISSION = 0
  SUBSTITUTION = 1
  INSERTION = 2

  def __repr__(self):
    if self == self.OMISSION:
      return str("Omission")
    if self == self.SUBSTITUTION:
      return str("Substitution")
    if self == self.INSERTION:
      return str("Insertion")
    assert False


@dataclass
class WordEntry:
  graphemes: List[str]
  phonemes: List[str]
  phones: List[str]

  @property
  def graphemes_str(self):
    return ''.join(self.graphemes)


@dataclass
class Rule():
  rule_type: RuleType
  word: WordEntry
  positions: List[int]
  from_symbols: List[str]
  to_symbols: List[str]


def get_info(a: List[str], b: List[str]):
  res = ndiff(a, b)
  change_values = {}
  change_types = {}
  for change_pos, change in enumerate(res):
    change_type = change[:2]
    change_value = change[2:]
    if change_type == "  ":
      continue
    elif change_type == "+ " or change_type == "- ":
      change_types[change_pos] = change_type
      change_values[change_pos] = change_value
    else:
      assert False
  if len(change_values) == 0:
    return
  clusters = []
  last_pos = None
  current_cluster = []
  for pos in change_values.keys():
    if last_pos is None:
      current_cluster = [pos]
    else:
      if pos == last_pos + 1:
        current_cluster.append(pos)
      else:
        clusters.append(current_cluster)
        current_cluster = [pos]
    last_pos = pos
  clusters.append(current_cluster)
  a_str = ''.join(a)
  b_str = ''.join(b)
  for i, cluster in enumerate(clusters):
    #print(f"Cluster {i+1}/{len(clusters)}")
    cluster_types = [change_types[x] for x in cluster]
    cluster_values = [change_values[x] for x in cluster]
    unique_cluster_types = OrderedSet(cluster_types)
    if unique_cluster_types == OrderedSet(["+ "]):
      print(
        f"Insertion of \"{''.join(cluster_values)}\" in word \"{a_str}\" on position(s) {', '.join(list(map(str, cluster)))} -> \"{b_str}\"")
    elif unique_cluster_types == OrderedSet(["- "]):
      print(
        f"Omission of \"{''.join(cluster_values)}\" in word \"{a_str}\" on position(s) {', '.join(list(map(str, cluster)))} -> \"{b_str}\"")
    else:
      add_del = unique_cluster_types == OrderedSet(["+ ", "- "])
      del_add = unique_cluster_types == OrderedSet(["- ", "+ "])
      if add_del or del_add:
        from_w = ""
        to_w = ""
        for x_type, x_val, x_pos in zip(cluster_types, cluster_values, cluster):
          if x_type == "- ":
            from_w += x_val
          else:
            to_w += x_val
        print(
          f"Substitution of \"{from_w}\" to \"{to_w}\" in word \"{a_str}\" on position(s) {', '.join(list(map(str, cluster)))} -> \"{b_str}\"")
      else:
        assert False


def df_to_data(data: DataFrame, ipa_settings: IPAExtractionSettings) -> List[WordEntry]:
  res = []
  logger = getLogger(__name__)
  for i, row in data.iterrows():
    row_lang = row["lang"]
    valid_lang = is_lang_from_str_supported(row_lang)
    if not valid_lang:
      logger.error(f"Language {row_lang} is not supported!")
    lang = get_lang_from_str(row_lang)
    if lang != Language.ENG:
      logger.error(f"Language {row_lang} is not supported!")
    graphemes = text_to_symbols(row["graphemes"], lang=Language.ENG,
                                ipa_settings=None, logger=logger)
    phonemes = text_to_symbols(row["phonemes"], lang=Language.IPA,
                               ipa_settings=ipa_settings, logger=logger)
    phones = text_to_symbols(row["phones"], lang=Language.IPA,
                             ipa_settings=ipa_settings, logger=logger)

    entry = WordEntry(
        graphemes=graphemes,
        phonemes=phonemes,
        phones=phones,
    )
    res.append(entry)
  return res


def parse_eng_data(words: List[WordEntry]):
  for word in words:
    get_info(word.phonemes, word.phones)
