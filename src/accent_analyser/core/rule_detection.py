
from collections import Counter, OrderedDict
from dataclasses import dataclass, field
from difflib import ndiff
from enum import IntEnum
from logging import StrFormatStyle, getLogger
from typing import Dict, Iterable, List, Optional
from typing import OrderedDict as OrderedDictType
from typing import Tuple

from ordered_set import OrderedSet
from pandas import DataFrame
from text_utils import IPAExtractionSettings, Language, text_to_symbols
from text_utils.language import get_lang_from_str, is_lang_from_str_supported


class RuleType(IntEnum):
  OMISSION = 0
  SUBSTITUTION = 1
  INSERTION = 2
  NOTHING = 3

  def __repr__(self):
    if self == self.OMISSION:
      return str("Omission")
    if self == self.SUBSTITUTION:
      return str("Substitution")
    if self == self.INSERTION:
      return str("Insertion")
    if self == self.NOTHING:
      return str("Nothing")
    assert False


class ChangeType(IntEnum):
  ADD = 0
  REMOVE = 1


@dataclass  # (eq=True, frozen=True)
class WordEntry:
  graphemes: List[str]
  phonemes: List[str]
  phones: List[str]

  @property
  def graphemes_str(self) -> str:
    return ''.join(self.graphemes)

  @property
  def phonemes_str(self) -> str:
    return ''.join(self.phonemes)

  @property
  def phones_str(self) -> str:
    return ''.join(self.phones)

  @property
  def is_empty(self) -> bool:
    return self.graphemes == self.phonemes == self.phones == []

  def __hash__(self) -> int:
    return hash((tuple(self.graphemes), tuple(self.phonemes), tuple(self.phones)))


@dataclass()  # (eq=True, frozen=True)
class Rule():
  rule_type: RuleType = RuleType.NOTHING
  positions: List[int] = field(default_factory=list)
  from_symbols: List[str] = field(default_factory=list)
  to_symbols: List[str] = field(default_factory=list)

  @property
  def from_str(self) -> str:
    return ''.join(self.from_symbols)

  @property
  def to_str(self) -> str:
    return ''.join(self.to_symbols)

  @property
  def positions_str(self) -> str:
    return ','.join(list(map(str, self.positions)))

  def __str__(self) -> str:
    if self.rule_type == RuleType.OMISSION:
      return f"O({self.from_str};{self.positions_str})"
    if self.rule_type == RuleType.INSERTION:
      return f"I({self.to_str};{self.positions_str})"
    if self.rule_type == RuleType.SUBSTITUTION:
      return f"S({self.from_str};{self.to_str};{self.positions_str})"
    if self.rule_type == RuleType.NOTHING:
      return ""
    assert False

  def __hash__(self) -> int:
    return hash((tuple(self.from_symbols), tuple(self.to_symbols), tuple(self.positions), self.rule_type))


@dataclass()  # (eq=True, frozen=True)
class Change():
  change: str
  change_type: ChangeType


def clustered_changes_to_rules(clustered_changes: List[OrderedDictType[int, Change]]) -> Tuple[Rule]:
  rules = []
  if len(clustered_changes) == 0:
    rules.append(Rule())
  else:
    for changes_cluster in clustered_changes:
      rule = changes_cluster_to_rule(changes_cluster)
      rules.append(rule)
  rules_tuple = tuple(rules)
  return rules_tuple


def get_rules(words: List[WordEntry]) -> OrderedDictType[WordEntry, List[Tuple[Rule]]]:
  rules_dict: OrderedDictType[WordEntry, List[Rule]] = OrderedDict()
  for word in words:
    assert not word.is_empty
    if word not in rules_dict:
      rules_dict[word] = []
    changes = get_ndiff_info(word.phonemes, word.phones)
    clustered_changes = cluster_changes(changes)
    rules_tuple = clustered_changes_to_rules(clustered_changes)
    rules_dict[word].append(rules_tuple)
  return rules_dict


def get_ndiff_info(l1: List[str], l2: List[str]) -> OrderedDictType[int, Change]:
  res = ndiff(l1, l2)
  result: OrderedDictType[int, Change] = OrderedDict()
  for change_pos, change in enumerate(res):
    change_type = change[:2]
    change_value = change[2:]
    if change_type == "  ":
      continue
    else:
      change = Change(
        change=change_value,
        change_type=ChangeType.ADD if change_type == "+ " else ChangeType.REMOVE,
      )
      result[change_pos] = change
  return result


def cluster_changes(changes: OrderedDictType[int, Change]) -> List[OrderedDictType[int, Change]]:
  if len(changes) == 0:
    return []

  clusters = []
  last_pos = None
  current_cluster = OrderedDict()
  for pos, change in changes.items():
    if last_pos is None:
      current_cluster[pos] = change
    else:
      if pos == last_pos + 1:
        current_cluster[pos] = change
      else:
        clusters.append(current_cluster)
        current_cluster = OrderedDict()
        current_cluster[pos] = change
    last_pos = pos

  assert len(current_cluster) > 0
  clusters.append(current_cluster)

  return clusters


def changes_cluster_to_rule(cluster: OrderedDictType[int, Change]) -> Rule:
  assert len(cluster) > 0

  cluster_types = [change.change_type for _, change in cluster.items()]
  cluster_changed_symbols = [change.change for _, change in cluster.items()]
  unique_cluster_types = OrderedSet(cluster_types)

  rule_type: RuleType
  from_symbols: List[str] = []
  to_symbols: List[str] = []
  positions: List[int] = list(cluster.keys())

  if len(unique_cluster_types) == 1:
    if unique_cluster_types[0] == ChangeType.ADD:
      rule_type = RuleType.INSERTION
      to_symbols = cluster_changed_symbols
    else:
      assert unique_cluster_types[0] == ChangeType.REMOVE
      rule_type = RuleType.OMISSION
      from_symbols = cluster_changed_symbols
  else:
    assert len(unique_cluster_types) == 2
    rule_type = RuleType.SUBSTITUTION
    add_del = unique_cluster_types[0] == ChangeType.ADD
    del_add = unique_cluster_types[0] == ChangeType.REMOVE
    from_positions = []
    to_positions = []
    assert add_del or del_add
    for pos, change in cluster.items():
      if change.change_type == ChangeType.REMOVE:
        from_symbols.append(change.change)
        from_positions.append(pos)
      else:
        to_symbols.append(change.change)
        to_positions.append(pos)
    positions = to_positions if add_del else from_positions

  rule = Rule(
    from_symbols=from_symbols,
    to_symbols=to_symbols,
    positions=positions,
    rule_type=rule_type,
  )

  return rule


def print_rule(word: WordEntry, rule: Rule) -> None:
  logger = getLogger(__name__)
  if rule.rule_type == RuleType.INSERTION:
    logger.info(
      f"Insertion of \"{rule.to_str}\" in word \"{word.phonemes_str}\" ({word.graphemes_str}) on position(s) {rule.positions_str} -> \"{word.phones_str}\".")
  elif rule.rule_type == RuleType.OMISSION:
    logger.info(
      f"Omission of \"{rule.from_str}\" in word \"{word.phonemes_str}\" ({word.graphemes_str}) on position(s) {rule.positions_str} -> \"{word.phones_str}\".")
  elif rule.rule_type == RuleType.SUBSTITUTION:
    logger.info(
      f"Substitution of \"{rule.from_str}\" to \"{rule.to_str}\" in word \"{word.phonemes_str}\" ({word.graphemes_str}) on position(s) {rule.positions_str} -> \"{word.phones_str}\".")
  elif rule.rule_type == RuleType.NOTHING:
    logger.info(
      f"Nothing changed in word \"{word.phonemes_str}\" ({word.graphemes_str}).")
  else:
    assert False


def df_to_data(data: DataFrame, ipa_settings: IPAExtractionSettings) -> List[WordEntry]:
  res = []
  logger = getLogger(__name__)
  for _, row in data.iterrows():
    row_lang = row["lang"]
    valid_lang = is_lang_from_str_supported(row_lang)
    if not valid_lang:
      logger.error(f"Language {row_lang} is not supported!")
    lang = get_lang_from_str(row_lang)
    if lang != Language.ENG:
      logger.error(f"Language {row_lang} is not supported!")
    graphemes = text_to_symbols(row["graphemes"].strip(), lang=Language.ENG,
                                ipa_settings=None, logger=logger)
    phonemes = text_to_symbols(row["phonemes"].strip(), lang=Language.IPA,
                               ipa_settings=ipa_settings, logger=logger)
    phones = text_to_symbols(row["phones"].strip(), lang=Language.IPA,
                             ipa_settings=ipa_settings, logger=logger)

    entry = WordEntry(
        graphemes=graphemes,
        phonemes=phonemes,
        phones=phones,
    )

    if not entry.is_empty:
      res.append(entry)

  return res


def get_word_stats(word_rules: OrderedDictType[WordEntry, List[Tuple[Rule]]]) -> List[Tuple[WordEntry, Tuple[Rule], int, int]]:

  res = []
  for word, rules in word_rules.items():
    rule_counter = Counter(rules)

    for rule_tuple, count in rule_counter.items():
      res.append((
        word,
        rule_tuple,
        count,
        len(rules),
      ))

  return res


def sort_rules_after_positions(rules: Tuple[Rule]) -> Tuple[Rule]:
  res = tuple(sorted(rules, key=lambda x: tuple(x.positions)))
  return res


def word_stats_to_df(word_stats: List[Tuple[WordEntry, Tuple[Rule], int, int]]) -> DataFrame:
  resulting_csv_data = []
  for word, rules_tuple, count, total_count in word_stats:
    rules_str = ', '.join([str(x) for x in sort_rules_after_positions(rules_tuple)])
    resulting_csv_data.append((
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
    columns=["English", "Phonemes", "Phones", "Rules",
             "Occurrences", "Occurrences Total", "Occurrences (%)"],
  )

  return res


def sort_word_stats_df(resulting_csv_data: List[Tuple[str, str, str, str, int, int, str]]):
  ''' Sorts: English ASC, Phonemes ASC, Occurrences DESC, Rules ASC'''
  resulting_csv_data.sort(key=lambda x: (x[0], x[1], x[5] - x[4], x[3]))
