from typing import List
from typing import OrderedDict as OrderedDictType
from typing import Set, Tuple

from accent_analyser.core.rule_detectionv2 import (PhonemeOccurrences,
                                                   PhoneOccurrences, Rule,
                                                   WordEntry, WordRules,
                                                   rule_to_str, rules_to_str)
from pandas import DataFrame

RuleStatsEntry = Tuple[str, str, str, str, int, int, str]


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


def get_rule_stats(word_rules: OrderedDictType[WordEntry, WordRules], phone_occurrences: PhoneOccurrences) -> List[RuleStatsEntry]:
  res: List[Tuple[int, Rule, WordEntry, WordRules, int, int]] = []
  words_to_rules = word_rules_to_rules_dict(word_rules)

  for rule_id, (rule, words) in enumerate(words_to_rules.items()):
    rule_id_one_based = rule_id + 1
    rule_str = rule_to_str(rule, positions=None)
    total_occ = 0

    for word in words:
      total_occ += phone_occurrences[word]

    for word in words:
      #total_word_occ = phoneme_occurrences[(word.graphemes, word.phonemes)]
      phone_occ = phone_occurrences[word]
      rules = word_rules[word]
      occurrence_percent = phone_occ / total_occ * 100
      rules_str = rules_to_str(rules)

      res.append((
        rule_id_one_based,
        rule_str,
        word.graphemes_str,
        word.phonemes_str,
        word.phones_str,
        rules_str,
        phone_occ,
        total_occ,
        f"{occurrence_percent:.2f}",
      ))

  sort_rule_stats(res)

  return res


def sort_rule_stats(resulting_csv_data: List[RuleStatsEntry]):
  ''' Sorts: Nr ASC, Occurrences DESC, Phones ASC'''
  resulting_csv_data.sort(key=lambda x: (x[0], x[7] - x[6], x[4]))


def rule_stats_to_df(word_stats: List[RuleStatsEntry]) -> DataFrame:
  res = DataFrame(
    data=word_stats,
    columns=["Nr", "Rule", "English", "Phonemes", "Phones", "All Rules",
             "Occurrences", "Occurrences Total", "Occurrences (%)"],
  )

  return res
