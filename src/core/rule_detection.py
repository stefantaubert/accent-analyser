
from collections import Counter, OrderedDict
from dataclasses import dataclass
from difflib import ndiff
from enum import IntEnum
from logging import StrFormatStyle, getLogger
from typing import List, Optional
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


@dataclass(eq=True, frozen=True)
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


@dataclass(eq=True, frozen=True)
class Rule():
  rule_type: RuleType
  word: WordEntry
  positions: List[int]
  from_symbols: List[str]
  to_symbols: List[str]

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


def get_info(word: WordEntry) -> List[Rule]:
  res = ndiff(word.phonemes, word.phones)
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
  rules = []

  if len(current_cluster) > 0:
    clusters.append(current_cluster)

  if len(clusters) == 0:
    empty_rule = Rule(
      rule_type=RuleType.NOTHING,
      from_symbols=[],
      to_symbols=[],
      positions=[],
      word=word,
    )
    return [empty_rule]

  for cluster in clusters:
    #print(f"Cluster {i+1}/{len(clusters)}")
    cluster_types = [change_types[x] for x in cluster]
    cluster_values = [change_values[x] for x in cluster]
    unique_cluster_types = OrderedSet(cluster_types)
    rule_type: RuleType
    from_symbols: List[str]
    to_symbols: List[str]
    positions: List[int] = cluster
    if unique_cluster_types == OrderedSet(["+ "]):
      rule_type = RuleType.INSERTION
      from_symbols = []
      to_symbols = cluster_values
    elif unique_cluster_types == OrderedSet(["- "]):
      rule_type = RuleType.OMISSION
      from_symbols = cluster_values
      to_symbols = []
    else:
      rule_type = RuleType.SUBSTITUTION
      add_del = unique_cluster_types == OrderedSet(["+ ", "- "])
      del_add = unique_cluster_types == OrderedSet(["- ", "+ "])
      assert add_del or del_add
      from_symbols = []
      to_symbols = []
      for x_type, x_val, x_pos in zip(cluster_types, cluster_values, cluster):
        if x_type == "- ":
          from_symbols.append(x_val)
        else:
          to_symbols.append(x_val)

    rule = Rule(
      word=word,
      from_symbols=from_symbols,
      to_symbols=to_symbols,
      positions=positions,
      rule_type=rule_type,
    )

    rules.append(rule)
  return rules


def print_rules(rules: List[Rule]) -> None:
  logger = getLogger(__name__)
  for rule in rules:
    if rule.rule_type == RuleType.INSERTION:
      logger.info(
        f"Insertion of \"{rule.to_str}\" in word \"{rule.word.phonemes_str}\" ({rule.word.graphemes_str}) on position(s) {rule.positions_str} -> \"{rule.word.phones_str}\".")
    elif rule.rule_type == RuleType.OMISSION:
      logger.info(
        f"Omission of \"{rule.from_str}\" in word \"{rule.word.phonemes_str}\" ({rule.word.graphemes_str}) on position(s) {rule.positions_str} -> \"{rule.word.phones_str}\".")
    elif rule.rule_type == RuleType.SUBSTITUTION:
      logger.info(
       f"Substitution of \"{rule.from_str}\" to \"{rule.to_str}\" in word \"{rule.word.phonemes_str}\" ({rule.word.graphemes_str}) on position(s) {rule.positions_str} -> \"{rule.word.phones_str}\".")
    elif rule.rule_type == RuleType.NOTHING:
      logger.info(
        f"Nothing changed in word \"{rule.word.phonemes_str}\" ({rule.word.graphemes_str}).")
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
    res.append(entry)
  return res


def parse_eng_data(words: List[WordEntry]):
  all_rules = []
  rules_dict: OrderedDictType[Tuple[str, str], Tuple[str, str]] = OrderedDict()
  for word in words:
    if word.is_empty:
      continue
    rules = get_info(word)
    k = (word.graphemes_str, word.phonemes_str)
    if k not in rules_dict:
      rules_dict[k] = []
    rules_str = ', '.join(sorted([str(x) for x in rules]))
    rules_dict[k].append((word.phones_str, rules_str))
    all_rules.extend(rules)
  print_rules(all_rules)

  rules_unique: OrderedDictType[Tuple[str, str], List[Tuple[str, str]]] = OrderedDict()
  rules_probs: OrderedDictType[Tuple[str, str], List[float]] = OrderedDict()
  for k, r in rules_dict.items():
    c = Counter(r)
    unique_vals = [x for x, _ in c.most_common()]
    unique_probs = [(x, len(r)) for _, x in c.most_common()]
    rules_unique[k] = unique_vals
    rules_probs[k] = unique_probs

  resulting_csv_data = []
  for k, rules_str in rules_dict.items():
    graphemes_str, phonemes_str = k
    unique_r = rules_unique[k]
    probs_r = rules_probs[k]
    for i, (phones_str, rule_str) in enumerate(unique_r):
      occs, total_occs = probs_r[i]
      resulting_csv_data.append((
        graphemes_str,
        phonemes_str,
        phones_str,
        rule_str,
        f"{occs}",
        f"{total_occs}",
        f"{occs/total_occs*100:.2f}",
      ))

  resulting_csv_data.sort()

  res = DataFrame(
    data=resulting_csv_data,
    columns=["English", "Phonemes", "Phones", "Rules",
             "Occurrences", "Occurrences Total", "Occurrences (%)"],
  )

  return res

  res.to_csv("")
  rules_str: List[Tuple[str, str, str, str]] = []

  for r in [x for x in all_rules if x.rule_type == RuleType.NOTHING]:
    k = (r.word.graphemes_str, r.word.phonemes_str, r.word.phones_str, str(r))
    rules_str.append(k)

  for r in [x for x in all_rules if x.rule_type == RuleType.OMISSION]:
    k = (r.word.graphemes_str, r.word.phonemes_str, r.word.phones_str, str(r))
    rules_str.append(k)

  for r in [x for x in all_rules if x.rule_type == RuleType.INSERTION]:
    k = (r.word.graphemes_str, r.word.phonemes_str, r.word.phones_str, str(r))
    rules_str.append(k)

  for r in [x for x in all_rules if x.rule_type == RuleType.SUBSTITUTION]:
    k = (r.word.graphemes_str, r.word.phonemes_str, r.word.phones_str, str(r))
    rules_str.append(k)

  rules_str.sort()

  rules_dict: OrderedDictType[Tuple[str, str, str], str] = OrderedDict()

  for graphemes_str, phonemes_str, phones_str, rule_str in rules_str:
    k = (graphemes_str, phonemes_str, phones_str)
    if k not in rules_dict:
      rules_dict[k] = []
    rules_dict

  # print(rules_str)

  omission_words = {}
  for rule in omission_rules:
    if not rule.word.phonemes_str in omission_words:
      omission_words[rule.word.phonemes_str] = []
    omission_words[rule.word.phonemes_str].append(rule)
  omission_words_sorted: OrderedDictType[str, List[Rule]] = OrderedDict(
    {k: omission_words[k] for k in sorted(omission_words.keys())})
  logger = getLogger(__name__)

  for k, v in omission_words_sorted.items():
    v: List[Rule]
    omitted_symbols = {f"{x.from_str} ({x.positions_str})" for x in v}
    logger.info(f"{k}: {', '.join(list(sorted(omitted_symbols)))}")
