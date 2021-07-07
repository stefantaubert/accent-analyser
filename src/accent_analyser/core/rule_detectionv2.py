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

PROB_PRECISION_DECIMALS = 6
STRIP_SYMBOLS = list(".?!,;-: ")

Graphemes = Tuple[str, ...]
Phonemes = Tuple[str, ...]
Phones = Tuple[str, ...]
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


@dataclass  # (eq=True, frozen=True)
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


def get_indicies_as_str(indicies: Tuple[int, ...]):
  if len(indicies) <= 2:
    return ','.join(list(map(str, indicies)))
  else:
    return f"{indicies[0]}-{indicies[-1]}"


@dataclass()
class Rule():
  rule_type: RuleType
  from_symbols: Tuple[str]
  to_symbols: Tuple[str]

  @property
  def from_str(self) -> str:
    return ''.join(self.from_symbols)

  @property
  def to_str(self) -> str:
    return ''.join(self.to_symbols)

  def __hash__(self) -> int:
    return hash((self.from_symbols, self.to_symbols, self.rule_type))


WordRules = OrderedDictType[Positions, Rule]


UNCHANGED_RULE = "Unchanged"


def rule_to_str(rule: Optional[Rule], positions: Optional[Positions]):
  if rule is None:
    return UNCHANGED_RULE

  positions_str = ""
  if positions is None:
    positions_str = f";{get_indicies_as_str(positions)}"

  if rule.rule_type == RuleType.OMISSION:
    return f"O({rule.from_str}{positions_str})"
  if rule.rule_type == RuleType.INSERTION:
    return f"I({rule.to_str}{positions_str})"
  if rule.rule_type == RuleType.SUBSTITUTION:
    return f"S({rule.from_str};{rule.to_str}{positions_str})"
  assert False


def rules_to_str(rules: WordRules) -> str:
  if len(rules) == 0:
    return UNCHANGED_RULE
  tmp = []
  for positions, rule in rules.items():
    rule_str = rule_to_str(rule, positions)
    tmp.append(rule_str)
  res = ", ".join(tmp)
  return res


@dataclass()  # (eq=True, frozen=True)
class Change():
  change: str
  change_type: ChangeType


PhoneOccurrences = OrderedDictType[WordEntry, int]
PhonemeOccurrences = OrderedDictType[Tuple[Graphemes, Phonemes], int]


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
    graphemes = text_to_symbols(str(row["graphemes"]), lang=Language.ENG,
                                ipa_settings=None, logger=logger)
    phonemes = text_to_symbols(str(row["phonemes"]), lang=Language.IPA,
                               ipa_settings=ipa_settings, logger=logger)
    phones = text_to_symbols(str(row["phones"]), lang=Language.IPA,
                             ipa_settings=ipa_settings, logger=logger)

    graphemes = strip_word(symbols_to_lower(graphemes), symbols=STRIP_SYMBOLS)
    phonemes = strip_word(phonemes, symbols=STRIP_SYMBOLS)
    phones = strip_word(phones, symbols=STRIP_SYMBOLS)

    entry = WordEntry(
        graphemes=graphemes,
        phonemes=phonemes,
        phones=phones,
    )

    if not entry.is_empty:
      res.append(entry)

  return res


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
    # TODO: reevaluate
    if del_add:
      positions = from_positions
    else:
      # if len(to_positions) > 1:
      #   print()
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
    changes = get_ndiff_info(word.phonemes, word.phones)
    clustered_changes = cluster_changes(changes)
    rules = clustered_changes_to_rules(clustered_changes)
    rules_dict[word] = rules
  return rules_dict


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
  else:
    assert False


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


def word_rules_to_rules_dict(word_rules: OrderedDictType[WordEntry, WordRules]) -> OrderedDictType[Rule, List[WordEntry]]:
  all_rules: Set[Rule] = {x for y in word_rules.values() for x in y.values()}
  words_to_rules: OrderedDictType[Rule, List[WordEntry]] = dict()

  for rule in all_rules:
    for word, rules in word_rules.items():
      if rule in rules.values():
        if rule not in words_to_rules:
          words_to_rules[rule] = []
        words_to_rules[rule].append(word)

  words_to_rules[None] = []

  for word, rules in word_rules.items():
    if len(rules) == 0:
      words_to_rules[None].append(word)

  return words_to_rules


RuleStatsEntry = Tuple[int, Rule, WordEntry, WordRules, int, int]


def get_rule_stats(word_rules: OrderedDictType[WordEntry, WordRules], phone_occurrences: PhoneOccurrences, phoneme_occurrences: PhonemeOccurrences) -> List[RuleStatsEntry]:
  res: List[Tuple[int, Rule, WordEntry, WordRules, int, int]] = []
  words_to_rules = word_rules_to_rules_dict(word_rules)

  for i, (rule, words) in enumerate(words_to_rules.items()):
    for word in words:
      total_occ = phoneme_occurrences[(word.graphemes, word.phonemes)]
      phone_occ = phone_occurrences[word]
      word_rules = word_rules[word]
      res.append((
        i,
        rule,
        word,
        word_rules,
        phone_occ,
        total_occ,
      ))

  return res


def rule_stats_to_df(word_stats: List[RuleStatsEntry]) -> DataFrame:
  resulting_csv_data = []
  for i, rule, word_entry, word_rules, count, total_count in word_stats:
    rule_str = rule_to_str(rule, None)
    rules_str = rules_to_str(word_rules)
    resulting_csv_data.append((
      i + 1,
      rule_str,
      word_entry.graphemes_str,
      word_entry.phonemes_str,
      word_entry.phones_str,
      rules_str,
      count,
      total_count,
      f"{count/total_count*100:.2f}",
    ))

  sort_rule_stats_df(resulting_csv_data)

  res = DataFrame(
    data=resulting_csv_data,
    columns=["Nr", "Rule", "English", "Phonemes", "Phones", "All Rules",
             "Occurrences", "Occurrences Total", "Occurrences (%)"],
  )

  return res


def sort_rule_stats_df(resulting_csv_data: List[Tuple[str, str, str, str, int, int, str]]):
  ''' Sorts: Nr ASC, Occurrences DESC, Phones ASC'''
  resulting_csv_data.sort(key=lambda x: (x[0], x[7] - x[6], x[4]))



def symbols_to_str_with_space(symbols: List[str]) -> str:
  return " ".join(symbols)


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
