from collections import OrderedDict

from accent_analyser.core.rule_detection import Rule, RuleType, WordEntry
from accent_analyser.core.rule_stats import (get_rule_stats, rule_stats_to_df,
                                             sort_rule_stats)


def test_get_rule_stats__one_word_one_rule():
  word1 = WordEntry(
    graphemes=("a",),
    phonemes=("b",),
    phones=("c",),
  )

  rule1 = Rule(
    rule_type=RuleType.INSERTION,
    from_symbols=(),
    to_symbols=("a",),
  )

  word_rules1 = OrderedDict({
    (0,): rule1,
  })

  word_rules = OrderedDict({
    word1: word_rules1,
  })

  phone_occurrences = OrderedDict({
    word1: 4,
  })

  phoneme_occurrences = OrderedDict({
    (word1.graphemes, word1.phonemes): 6,
  })

  res = get_rule_stats(word_rules, phone_occurrences, phoneme_occurrences)

  assert len(res) == 1
  assert res[0] == (0, rule1, word1, word_rules1, 4, 6)


def test_get_rule_stats__no_rules():
  word1 = WordEntry(
    graphemes=("a",),
    phonemes=("b",),
    phones=("c",),
  )

  word_rules1 = OrderedDict()

  word_rules = OrderedDict({
    word1: word_rules1,
  })

  phone_occurrences = OrderedDict({
    word1: 4,
  })

  phoneme_occurrences = OrderedDict({
    (word1.graphemes, word1.phonemes): 6,
  })

  res = get_rule_stats(word_rules, phone_occurrences, phoneme_occurrences)

  assert len(res) == 1
  assert res[0] == (0, None, word1, word_rules1, 4, 6)


def test_rule_stats_to_df():
  word1 = WordEntry(
    graphemes=("a",),
    phonemes=("b",),
    phones=("c",),
  )

  rule1 = Rule(
    rule_type=RuleType.INSERTION,
    from_symbols=(),
    to_symbols=("a",),
  )

  word_rules1 = OrderedDict({
    (0,): rule1,
  })

  rule_stats = [(0, rule1, word1, word_rules1, 4, 5)]

  res = rule_stats_to_df(rule_stats)

  assert len(res) == 1
  assert list(res.columns) == ["Nr", "Rule", "English", "Phonemes", "Phones", "All Rules",
                               "Occurrences", "Occurrences Total", "Occurrences (%)"]
  assert list(res.iloc[0]) == [1, 'I(a)', 'a', 'b', 'c', 'I(a;1)', 4, 5, '80.00']


def test_sort_rule_stats_df():
  resulting_csv_data = [
    (1, "ruleB", "a", "b", "a", "ruleB", 1, 4, "75.00"),
    (1, "ruleC", "a", "b", "c", "ruleC", 2, 4, "75.00"),
    (1, "ruleA", "a", "b", "b", "ruleA", 1, 4, "75.00"),
    (0, "rule1", "a", "a", "a", "rule1", 1, 4, "75.00"),
  ]

  sort_rule_stats(resulting_csv_data)

  assert len(resulting_csv_data) == 4
  assert resulting_csv_data[0] == (0, "rule1", "a", "a", "a", "rule1", 1, 4, "75.00")
  assert resulting_csv_data[1] == (1, "ruleC", "a", "b", "c", "ruleC", 2, 4, "75.00")
  assert resulting_csv_data[2] == (1, "ruleB", "a", "b", "a", "ruleB", 1, 4, "75.00")
  assert resulting_csv_data[3] == (1, "ruleA", "a", "b", "b", "ruleA", 1, 4, "75.00")
