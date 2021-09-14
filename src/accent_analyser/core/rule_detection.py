from collections import OrderedDict
from dataclasses import dataclass
from difflib import ndiff
from enum import IntEnum
from logging import getLogger
from typing import List, Optional
from typing import OrderedDict as OrderedDictType
from typing import Tuple

from ordered_set import OrderedSet
from pandas import DataFrame
from text_utils import (Language, SymbolFormat, Symbols, get_lang_from_str,
                        text_to_symbols)
from text_utils.language import is_lang_from_str_supported
from text_utils.utils import symbols_strip, symbols_to_lower

PROB_PRECISION_DECIMALS = 6
# TODO: remove space symbol
STRIP_SYMBOLS = list(".?!,;-: ")
UNCHANGED_RULE = "Unchanged"

Graphemes = Symbols
Phonemes = Symbols
Phones = Symbols
Positions = Tuple[int, ...]


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


class ChangeType(IntEnum):
  ADD = 0
  REMOVE = 1


@dataclass()
class WordEntry:
  graphemes: Graphemes
  phonemes: Phonemes
  phones: Phones

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
    return len(self.graphemes) == len(self.phonemes) == len(self.phones) == 0

  def __hash__(self) -> int:
    return hash((self.graphemes, self.phonemes, self.phones))


@dataclass()
class Rule():
  rule_type: RuleType
  from_symbols: Symbols
  to_symbols: Symbols

  @property
  def from_str(self) -> str:
    return ''.join(self.from_symbols)

  @property
  def to_str(self) -> str:
    return ''.join(self.to_symbols)

  def __hash__(self) -> int:
    return hash((self.from_symbols, self.to_symbols, self.rule_type))


WordRules = OrderedDictType[Positions, Rule]
PhoneOccurrences = OrderedDictType[WordEntry, int]
PhonemeOccurrences = OrderedDictType[Tuple[Graphemes, Phonemes], int]


def positions_to_str(positions: Positions) -> str:
  if len(positions) <= 2:
    return ','.join(list(map(str, positions)))
  else:
    return f"{positions[0]}-{positions[-1]}"


def rule_to_str(rule: Optional[Rule], positions: Optional[Positions]) -> str:
  if rule is None:
    return UNCHANGED_RULE

  positions_str = ""
  if positions is not None:
    positions_str = f";{positions_to_str(positions)}"

  if rule.rule_type == RuleType.OMISSION:
    return f"O({rule.from_str}{positions_str})"
  if rule.rule_type == RuleType.INSERTION:
    return f"I({rule.to_str}{positions_str})"
  if rule.rule_type == RuleType.SUBSTITUTION:
    return f"S({rule.from_str};{rule.to_str}{positions_str})"
  assert False


def positions_to_one_based(positions: Positions) -> Positions:
  one_based_positions = [x + 1 for x in positions]
  return one_based_positions


def rules_to_str(rules: WordRules) -> str:
  if len(rules) == 0:
    return UNCHANGED_RULE
  tmp = []
  for positions, rule in rules.items():
    one_based_positions = positions_to_one_based(positions)
    rule_str = rule_to_str(rule, one_based_positions)
    tmp.append(rule_str)
  res = ", ".join(tmp)
  return res


@dataclass()
class Change():
  change: str
  change_type: ChangeType


def df_to_data(data: DataFrame) -> List[WordEntry]:
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
    graphemes = text_to_symbols(
      str(row["graphemes"]), text_format=SymbolFormat.GRAPHEMES, lang=Language.ENG)
    phonemes = text_to_symbols(
      str(row["phonemes"]), text_format=SymbolFormat.PHONEMES_IPA, lang=Language.ENG)
    phones = text_to_symbols(
      str(row["phones"]), text_format=SymbolFormat.PHONES_IPA, lang=Language.ENG)

    graphemes = symbols_strip(symbols_to_lower(graphemes), strip=STRIP_SYMBOLS)
    phonemes = symbols_strip(phonemes, strip=STRIP_SYMBOLS)
    phones = symbols_strip(phones, strip=STRIP_SYMBOLS)

    entry = WordEntry(
        graphemes=tuple(graphemes),
        phonemes=tuple(phonemes),
        phones=tuple(phones),
    )

    if not entry.is_empty:
      res.append(entry)

  return res


def get_changes(l1: List[str], l2: List[str]) -> OrderedDictType[int, Change]:
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


def changes_cluster_to_rule(cluster: OrderedDictType[int, Change]) -> Tuple[Positions, Rule]:
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
    if del_add:
      positions = from_positions
    else:
      positions = [x - len(to_positions) for x in from_positions]

    assert len(positions) == len(from_symbols)

  rule = Rule(
    from_symbols=tuple(from_symbols),
    to_symbols=tuple(to_symbols),
    rule_type=rule_type,
  )

  return tuple(positions), rule


def clustered_changes_to_rules(clustered_changes: List[OrderedDictType[int, Change]]) -> WordRules:
  rules: WordRules = dict()
  if len(clustered_changes) > 0:
    tmp = []
    for changes_cluster in clustered_changes:
      positions, rule = changes_cluster_to_rule(changes_cluster)
      tmp.append((positions, rule))

    tmp.sort(key=lambda x: x[0])

    for positions, rule in tmp:
      assert positions not in rules
      rules[positions] = rule
  return rules


def get_phone_occurrences(words: List[WordEntry]) -> PhoneOccurrences:
  words_dict: PhoneOccurrences = OrderedDict()
  for w in words:
    if w not in words_dict:
      words_dict[w] = 0
    words_dict[w] += 1
  return words_dict


def get_phoneme_occurrences(words: List[WordEntry]) -> PhonemeOccurrences:
  result: PhonemeOccurrences = OrderedDict()
  for word_combi in words:
    k = (word_combi.graphemes, word_combi.phonemes)
    if k not in result:
      result[k] = 0
    result[k] += 1
  return result


def get_rules_from_words(words: OrderedSet[WordEntry]) -> OrderedDictType[WordEntry, WordRules]:
  rules_dict: OrderedDictType[WordEntry, WordRules] = OrderedDict()
  for word in words:
    changes = get_changes(word.phonemes, word.phones)
    clustered_changes = cluster_changes(changes)
    rules = clustered_changes_to_rules(clustered_changes)
    rules_dict[word] = rules
  return rules_dict


# def print_rule(word: WordEntry, rule: Rule) -> None:
#   logger = getLogger(__name__)
#   if rule.rule_type == RuleType.INSERTION:
#     logger.info(
#       f"Insertion of \"{rule.to_str}\" in word \"{word.phonemes_str}\" ({word.graphemes_str}) on position(s) {rule.positions_str} -> \"{word.phones_str}\".")
#   elif rule.rule_type == RuleType.OMISSION:
#     logger.info(
#       f"Omission of \"{rule.from_str}\" in word \"{word.phonemes_str}\" ({word.graphemes_str}) on position(s) {rule.positions_str} -> \"{word.phones_str}\".")
#   elif rule.rule_type == RuleType.SUBSTITUTION:
#     logger.info(
#       f"Substitution of \"{rule.from_str}\" to \"{rule.to_str}\" in word \"{word.phonemes_str}\" ({word.graphemes_str}) on position(s) {rule.positions_str} -> \"{word.phones_str}\".")
#   else:
#     assert False
