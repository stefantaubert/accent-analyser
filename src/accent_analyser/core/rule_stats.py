from typing import List
from typing import OrderedDict as OrderedDictType
from typing import Set, Tuple

from accent_analyser.core.rule_detectionv2 import (PhonemeOccurrences,
                                                   PhoneOccurrences, Rule,
                                                   WordEntry, WordRules,
                                                   rule_to_str, rules_to_str)
from pandas import DataFrame

RuleStatsEntry = Tuple[int, Rule, WordEntry, WordRules, int, int]


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
