from collections import OrderedDict

from accent_analyser.core.rule_detection import Rule, RuleType, WordEntry
from accent_analyser.core.word_stats import (get_word_stats, sort_word_stats,
                                             word_stats_to_df)


def test_get_word_stats__one_word_one_rule():
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
    word1: 1,
  })

  phoneme_occurrences = OrderedDict({
    (word1.graphemes, word1.phonemes): 1,
  })

  res = get_word_stats(word_rules, phone_occurrences, phoneme_occurrences)

  assert len(res) == 1
  assert res[0] == (1, "a", "b", "c", "I(a;1)", 1, 1, "100.00")


def test_get_word_stats__no_rules():
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

  res = get_word_stats(word_rules, phone_occurrences, phoneme_occurrences)

  assert len(res) == 1
  assert res[0] == (1, "a", "b", "c", "Unchanged", 4, 6, "66.67")


def test_get_word_stats__one_word_one_rule__multiple_occurrences():
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
    word1: 2,
  })

  phoneme_occurrences = OrderedDict({
    (word1.graphemes, word1.phonemes): 8,
  })

  res = get_word_stats(word_rules, phone_occurrences, phoneme_occurrences)

  assert len(res) == 1
  assert res[0] == (1, "a", "b", "c", "I(a;1)", 2, 8, "25.00")


def test_get_word_stats__two_words_one_rule():
  word1 = WordEntry(
    graphemes=("a",),
    phonemes=("b",),
    phones=("c",),
  )

  word2 = WordEntry(
    graphemes=("a",),
    phonemes=("c",),
    phones=("d",),
  )

  rule1 = Rule(
    rule_type=RuleType.INSERTION,
    from_symbols=(),
    to_symbols=("a",),
  )

  word_rules1 = OrderedDict({
    (0,): rule1,
  })

  word_rules2 = OrderedDict({
    (5,): rule1,
  })

  word_rules = OrderedDict({
    word1: word_rules1,
    word2: word_rules2,
  })

  phone_occurrences = OrderedDict({
    word1: 2,
    word2: 8,
  })

  phoneme_occurrences = OrderedDict({
    (word1.graphemes, word1.phonemes): 8,
    (word2.graphemes, word2.phonemes): 16,
  })

  res = get_word_stats(word_rules, phone_occurrences, phoneme_occurrences)

  assert len(res) == 2
  assert res[0] == (1, "a", "b", "c", "I(a;1)", 2, 8, "25.00")
  assert res[1] == (2, "a", "c", "d", "I(a;6)", 8, 16, "50.00")


def test_get_word_stats__same_graphemes_and_phonemes_get_same_id():
  word1 = WordEntry(
    graphemes=("a",),
    phonemes=("b",),
    phones=("c",),
  )

  word2 = WordEntry(
    graphemes=("a",),
    phonemes=("b",),
    phones=("d",),
  )

  rule1 = Rule(
    rule_type=RuleType.INSERTION,
    from_symbols=(),
    to_symbols=("a",),
  )

  word_rules1 = OrderedDict({
    (0,): rule1,
  })

  word_rules2 = OrderedDict({
    (0,): rule1,
  })

  word_rules = OrderedDict({
    word1: word_rules1,
    word2: word_rules2,
  })

  phone_occurrences = OrderedDict({
    word1: 1,
    word2: 1,
  })

  phoneme_occurrences = OrderedDict({
    (word1.graphemes, word1.phonemes): 1,
    (word2.graphemes, word2.phonemes): 1,
  })

  res = get_word_stats(word_rules, phone_occurrences, phoneme_occurrences)

  assert len(res) == 2
  assert res[0][0] == 1
  assert res[1][0] == 1


def test_word_stats_to_df__sets_correct_columns():
  res = word_stats_to_df([])

  assert len(res) == 0
  assert list(res.columns) == ["Nr", "English", "Phonemes", "Phones", "Rules",
                               "Occurrences", "Occurrences Total", "Occurrences (%)"]


def test_word_stats_to_df__returns_data():
  word_stats = [(1, 'a', 'b', 'c', 'I(a;2)', 3, 4, '75.00')]

  res = word_stats_to_df(word_stats)

  assert len(res) == 1
  assert list(res.iloc[0]) == [1, 'a', 'b', 'c', 'I(a;2)', 3, 4, '75.00']


def test_sort_word_stats_df__sorts_correctly():
  resulting_csv_data = [
    (1, "a", "b", "a", "ruleB", 1, 4, "25.00"),
    (1, "a", "b", "c", "ruleC", 2, 4, "50.00"),
    (1, "a", "b", "b", "ruleA", 1, 4, "25.00"),
    (0, "a", "a", "a", "rule1", 1, 4, "25.00"),
  ]

  sort_word_stats(resulting_csv_data)

  assert len(resulting_csv_data) == 4
  assert resulting_csv_data[0] == (0, "a", "a", "a", "rule1", 1, 4, "25.00")
  assert resulting_csv_data[1] == (1, "a", "b", "c", "ruleC", 2, 4, "50.00")
  assert resulting_csv_data[2] == (1, "a", "b", "a", "ruleB", 1, 4, "25.00")
  assert resulting_csv_data[3] == (1, "a", "b", "b", "ruleA", 1, 4, "25.00")
