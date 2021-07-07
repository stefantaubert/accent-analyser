import random
from collections import OrderedDict

import numpy as np
from accent_analyser.core.rule_detectionv2 import (
    Change, ChangeType, Rule, RuleType, WordEntry, changes_cluster_to_rule,
    check_probabilities_are_valid, cluster_changes, df_to_data,
    get_indicies_as_str, get_ndiff_info, get_probabilities, get_rule_stats,
    get_word_stats, parse_probabilities_df, probabilities_to_df,
    replace_with_prob, rule_stats_to_df, sort_rule_stats_df,
    sort_word_stats_df, symbols_to_str_with_space, word_stats_to_df)
from pandas.core.frame import DataFrame
from text_utils import Language
from text_utils.ipa2symb import IPAExtractionSettings


def test_get_rules__nothing():
  word1 = WordEntry(
      graphemes=["a"],
      phonemes=["a"],
      phones=["a"],
    )
  words = [word1]
  res = get_rules(words)

  assert len(res) == 1
  assert res == OrderedDict({
    word1: [(
      Rule(
        from_symbols=[],
        to_symbols=[],
        positions=[],
        rule_type=RuleType.NOTHING,
      ),
    )],
  })


def test_get_rules__one_word():
  word1 = WordEntry(
      graphemes=["a"],
      phonemes=["b"],
      phones=["c"],
    )
  words = [word1]
  res = get_rules(words)

  assert len(res) == 1
  assert res == OrderedDict({
    word1: [(
      Rule(
        from_symbols=["b"],
        to_symbols=["c"],
        positions=[0],
        rule_type=RuleType.SUBSTITUTION,
      ),
    )],
  })


def test_get_rules__two_words():
  word1 = WordEntry(
      graphemes=["a"],
      phonemes=["b"],
      phones=["c"],
    )
  words = [word1, word1]
  res = get_rules(words)

  assert res == OrderedDict({
    word1: [(
      Rule(
        from_symbols=["b"],
        to_symbols=["c"],
        positions=[0],
        rule_type=RuleType.SUBSTITUTION,
      ),
    ),
        (
      Rule(
        from_symbols=["b"],
        to_symbols=["c"],
        positions=[0],
        rule_type=RuleType.SUBSTITUTION,
      ),
    ),
    ],
  })

# region get_ndiff_info


def test_get_ndiff_info__substitution__remove_add():
  res = get_ndiff_info(
    ["a"],
    ["c"]
  )

  assert res == OrderedDict({
    0: Change("a", ChangeType.REMOVE),
    1: Change("c", ChangeType.ADD),
  })


def test_get_ndiff_info__substitution__add_remove():
  res = get_ndiff_info(
    ['a', 'b'],
    ['c']
  )

  assert res == OrderedDict({
    0: Change("c", ChangeType.ADD),
    1: Change("a", ChangeType.REMOVE),
    2: Change("b", ChangeType.REMOVE),
  })


def test_get_ndiff_info__insertion():
  res = get_ndiff_info(["a"], ["a", "b"])

  assert res == OrderedDict({
    1: Change("b", ChangeType.ADD),
  })


def test_get_ndiff_info__omission():
  res = get_ndiff_info(["a"], [])

  assert res == OrderedDict({
    0: Change("a", ChangeType.REMOVE),
  })


def test_get_ndiff_info__nothing():
  res = get_ndiff_info(["a"], ["a"])

  assert res == OrderedDict()
# endregion

# region cluster_changes


def test_cluster_changes__zero_cluster():
  changes = OrderedDict()

  res = cluster_changes(changes)

  assert res == []


def test_cluster_changes__one_cluster():
  changes = OrderedDict({
    0: Change("a", ChangeType.REMOVE),
  })

  res = cluster_changes(changes)

  assert res == [
    OrderedDict({
        0: Change("a", ChangeType.REMOVE),
    })
  ]


def test_cluster_changes__two_clusters():
  changes = OrderedDict({
    0: Change("a", ChangeType.REMOVE),
    2: Change("a", ChangeType.REMOVE),
  })

  res = cluster_changes(changes)

  assert res == [
    OrderedDict({
        0: Change("a", ChangeType.REMOVE),
    }),
    OrderedDict({
        2: Change("a", ChangeType.REMOVE),
    })
  ]


def test_cluster_changes__two_clusters__coherent_are_merged():
  changes = OrderedDict({
    0: Change("a", ChangeType.REMOVE),
    1: Change("a", ChangeType.REMOVE),
    3: Change("a", ChangeType.REMOVE),
    4: Change("a", ChangeType.REMOVE),
  })

  res = cluster_changes(changes)

  assert res == [
    OrderedDict({
        0: Change("a", ChangeType.REMOVE),
        1: Change("a", ChangeType.REMOVE),
    }),
    OrderedDict({
        3: Change("a", ChangeType.REMOVE),
        4: Change("a", ChangeType.REMOVE),
    })
  ]

# endregion

# region changes_cluster_to_rule


def test_changes_cluster_to_rule__omission():
  changes = OrderedDict({
    0: Change("a", ChangeType.REMOVE),
  })

  res_pos, res_rule = changes_cluster_to_rule(changes)

  assert res_rule.rule_type == RuleType.OMISSION
  assert res_rule.from_symbols == ("a",)
  assert res_rule.to_symbols == ()
  assert res_pos == (0,)


def test_changes_cluster_to_rule__insertion():
  changes = OrderedDict({
    0: Change("a", ChangeType.ADD),
  })

  res_pos, res_rule = changes_cluster_to_rule(changes)

  assert res_rule.rule_type == RuleType.INSERTION
  assert res_rule.from_symbols == ()
  assert res_rule.to_symbols == ("a",)
  assert res_pos == (0,)


def test_changes_cluster_to_rule__substitution_add_remove():
  #from_w = ['s', 'm', 'ˈ', 'a', 'ɪ', 'l']
  #to_w = ['s', 'm', 'ˈ', 'e', 'l']

  #['p', 'ʌ', 't', 'ˈ', 'e', 'ɪ', 't', 'o', 'ʊ', 'z']
  #['p', 'ʌ', 't', 'ˈ', 'e', 'ɪ', 't', 'u', 's']
  changes = OrderedDict({
    0: Change("c", ChangeType.ADD),
    1: Change("a", ChangeType.REMOVE),
    2: Change("b", ChangeType.REMOVE),
  })

  res_pos, res_rule = changes_cluster_to_rule(changes)

  assert res_rule.rule_type == RuleType.SUBSTITUTION
  assert res_rule.from_symbols == ("a", "b",)
  assert res_rule.to_symbols == ("c",)
  assert res_pos == (0, 1,)


def test_changes_cluster_to_rule__substitution_remove_add():
  #from_w = ['h', 'ˈ', 'a', 'ʊ']
  #to_w =['x', 'ˈ', 'a', 'ʊ']
  changes = OrderedDict({
    0: Change("a", ChangeType.REMOVE),
    1: Change("b", ChangeType.ADD),
  })

  res_pos, res_rule = changes_cluster_to_rule(changes)

  assert res_rule.rule_type == RuleType.SUBSTITUTION
  assert res_rule.from_symbols == ("a",)
  assert res_rule.to_symbols == ("b",)
  assert res_pos == (0,)
# endregion


def test_get_word_stats__one_word_one_rule():
  word1 = WordEntry(
    graphemes=["a"],
    phonemes=["b"],
    phones=["c"],
  )
  rule1 = Rule(
    rule_type=RuleType.INSERTION,
    from_symbols=[],
    to_symbols=["a"],
    positions=[0],
  )

  word_rules = OrderedDict({
    word1: [(rule1,)],
  })

  res = get_word_stats(word_rules)

  assert len(res) == 1
  assert res[0] == (0, word1, (rule1,), 1, 1)


def test_get_word_stats__multiple_words_multiple_rules():
  word1_1 = WordEntry(
    graphemes=["a"],
    phonemes=["b"],
    phones=["c"],
  )
  word1_2 = WordEntry(
      graphemes=["a"],
      phonemes=["b"],
      phones=["d"],
  )
  word2 = WordEntry(
    graphemes=["a"],
    phonemes=["d"],
    phones=["e"],
  )

  rule1 = Rule(
    rule_type=RuleType.INSERTION,
    from_symbols=[],
    to_symbols=["a"],
    positions=[0],
  )

  rule2 = Rule(
    rule_type=RuleType.INSERTION,
    from_symbols=[],
    to_symbols=["b"],
    positions=[0],
  )

  word_rules = OrderedDict({
    word1_1: [(rule1,), (rule1,), (rule1,)],
    word1_2: [(rule1,), (rule1,)],
    word2: [(rule2,), (rule2,), (rule2,)],
  })

  res = get_word_stats(word_rules)

  assert len(res) == 3
  assert res[0] == (0, word1_1, (rule1,), 3, 5)
  assert res[1] == (0, word1_2, (rule1,), 2, 5)
  assert res[2] == (1, word2, (rule2,), 3, 3)


def test_rule_hash__same_content_is_equal():
  rule1 = Rule(
    rule_type=RuleType.INSERTION,
    from_symbols=[],
    to_symbols=["a"],
    positions=[0],
  )

  rule2 = Rule(
    rule_type=RuleType.INSERTION,
    from_symbols=[],
    to_symbols=["a"],
    positions=[0],
  )

  assert rule1 == rule2


def test_get_word_stats__multiple_rules_with_same_content_were_merged():
  word1 = WordEntry(
    graphemes=["a"],
    phonemes=["b"],
    phones=["c"],
  )

  rule1 = Rule(
    rule_type=RuleType.INSERTION,
    from_symbols=[],
    to_symbols=["a"],
    positions=[0],
  )

  rule2 = Rule(
    rule_type=RuleType.INSERTION,
    from_symbols=[],
    to_symbols=["a"],
    positions=[0],
  )

  word_rules = OrderedDict({
    word1: [(rule1,), (rule2,), (rule1,), (rule2,)],
  })

  res = get_word_stats(word_rules)

  assert len(res) == 1
  assert res[0] == (0, word1, (rule1,), 4, 4)


def test_get_word_stats__multiple_rules():
  word1 = WordEntry(
    graphemes=["a"],
    phonemes=["b"],
    phones=["c"],
  )

  word2 = WordEntry(
    graphemes=["a"],
    phonemes=["b"],
    phones=["e"],
  )

  rule1 = Rule(
    rule_type=RuleType.INSERTION,
    from_symbols=[],
    to_symbols=["a"],
    positions=[0],
  )

  word_rules = OrderedDict({
    word1: [(rule1,), (rule1,), (rule1,), (rule1,)],
    word2: [(rule1,)],
  })

  res = get_word_stats(word_rules)

  assert len(res) == 2
  assert res[0] == (0, word1, (rule1,), 4, 5)
  assert res[1] == (0, word2, (rule1,), 1, 5)


def test_word_stats_to_df():
  word1 = WordEntry(
    graphemes=["a"],
    phonemes=["b"],
    phones=["c"],
  )

  rule1 = Rule(
    rule_type=RuleType.INSERTION,
    from_symbols=[],
    to_symbols=["a"],
    positions=[0],
  )

  word_stats = [(0, word1, (rule1,), 3, 4)]
  res = word_stats_to_df(word_stats)

  assert len(res) == 1
  assert list(res.columns) == ["Nr", "English", "Phonemes", "Phones", "Rules",
                               "Occurrences", "Occurrences Total", "Occurrences (%)"]
  assert list(res.iloc[0]) == [1, 'a', 'b', 'c', 'I(a;1)', 3, 4, '75.00']


def test_sort_word_stats_df():
  resulting_csv_data = [
    (1, "a", "b", "a", "ruleB", 1, 4, "75.00"),
    (1, "a", "b", "c", "ruleC", 2, 4, "75.00"),
    (1, "a", "b", "b", "ruleA", 1, 4, "75.00"),
    (0, "a", "a", "a", "rule1", 1, 4, "75.00"),
  ]

  sort_word_stats_df(resulting_csv_data)

  assert len(resulting_csv_data) == 4
  assert resulting_csv_data[0] == (0, "a", "a", "a", "rule1", 1, 4, "75.00")
  assert resulting_csv_data[1] == (1, "a", "b", "c", "ruleC", 2, 4, "75.00")
  assert resulting_csv_data[2] == (1, "a", "b", "a", "ruleB", 1, 4, "75.00")
  assert resulting_csv_data[3] == (1, "a", "b", "b", "ruleA", 1, 4, "75.00")


def test_sort_rules_after_positions():
  r1 = Rule(from_symbols=["a"], positions=[0])
  r2 = Rule(from_symbols=["a"], positions=[0, 1])
  r3 = Rule(from_symbols=["a"], positions=[1, 2])
  r4 = Rule(from_symbols=["a"], positions=[4])
  rules = (r4, r2, r3, r1)

  res = sort_rules_after_positions(rules)

  assert res == (r1, r2, r3, r4)


def test_get_indicies_as_str__empty_list():
  res = get_indicies_as_str([])

  assert res == ""


def test_get_indicies_as_str__one_entry():
  res = get_indicies_as_str([1])

  assert res == "1"


def test_get_indicies_as_str__two_entries():
  res = get_indicies_as_str([1, 2])

  assert res == "1,2"


def test_get_indicies_as_str__three_entries():
  res = get_indicies_as_str([1, 2, 3])

  assert res == "1-3"


def test_get_rule_stats():
  word1 = WordEntry(
    graphemes=["a"],
    phonemes=["b"],
    phones=["c"],
  )

  word2 = WordEntry(
    graphemes=["a"],
    phonemes=["b"],
    phones=["e"],
  )

  rule1 = Rule(
    rule_type=RuleType.INSERTION,
    from_symbols=[],
    to_symbols=["a"],
    positions=[0],
  )

  word_rules = OrderedDict({
    word1: [(rule1,), (rule1,), (rule1,), (rule1,)],
    word2: [(rule1,)],
  })

  res = get_rule_stats(word_rules)

  assert_rule1 = Rule(
    rule_type=RuleType.INSERTION,
    from_symbols=[],
    to_symbols=["a"],
    positions=[],
  )

  assert len(res) == 2
  assert res[0] == (0, assert_rule1, word1, (rule1,), 4, 5)
  assert res[1] == (0, assert_rule1, word2, (rule1,), 1, 5)


def test_get_rule_stats__ignores_nothing_rule():
  word1 = WordEntry(
    graphemes=["a"],
    phonemes=["b"],
    phones=["c"],
  )

  rule1 = Rule(
    rule_type=RuleType.NOTHING,
    from_symbols=[],
    to_symbols=[],
    positions=[],
  )

  word_rules = OrderedDict({
    word1: [(rule1,), (rule1,), (rule1,), (rule1,)],
  })

  res = get_rule_stats(word_rules)

  assert len(res) == 0


def test_rule_stats_to_df():
  word1 = WordEntry(
    graphemes=["a"],
    phonemes=["b"],
    phones=["c"],
  )

  rule1 = Rule(
    rule_type=RuleType.INSERTION,
    from_symbols=[],
    to_symbols=["a"],
    positions=[0],
  )

  rule1_no_pos = Rule(
    rule_type=RuleType.INSERTION,
    from_symbols=[],
    to_symbols=["a"],
    positions=[],
  )

  rule_stats = [(1, rule1_no_pos, word1, (rule1,), 4, 5)]
  res = rule_stats_to_df(rule_stats)

  assert len(res) == 1
  assert list(res.columns) == ["Nr", "Rule", "English", "Phonemes", "Phones", "All Rules",
                               "Occurrences", "Occurrences Total", "Occurrences (%)"]
  assert list(res.iloc[0]) == [2, 'I(a)', 'a', 'b', 'c', 'I(a;1)', 4, 5, '80.00']


def test_sort_rule_stats_df():
  resulting_csv_data = [
    (1, "ruleB", "a", "b", "a", "ruleB", 1, 4, "75.00"),
    (1, "ruleC", "a", "b", "c", "ruleC", 2, 4, "75.00"),
    (1, "ruleA", "a", "b", "b", "ruleA", 1, 4, "75.00"),
    (0, "rule1", "a", "a", "a", "rule1", 1, 4, "75.00"),
  ]

  sort_rule_stats_df(resulting_csv_data)

  assert len(resulting_csv_data) == 4
  assert resulting_csv_data[0] == (0, "rule1", "a", "a", "a", "rule1", 1, 4, "75.00")
  assert resulting_csv_data[1] == (1, "ruleC", "a", "b", "c", "ruleC", 2, 4, "75.00")
  assert resulting_csv_data[2] == (1, "ruleB", "a", "b", "a", "ruleB", 1, 4, "75.00")
  assert resulting_csv_data[3] == (1, "ruleA", "a", "b", "b", "ruleA", 1, 4, "75.00")


def test_df_to_data():
  df = DataFrame(
    data=[
      ("A ", "a ", "a ", "ipa"),
    ],
    columns=["graphemes", "phonemes", "phones", "lang"],
  )

  res = df_to_data(df, ipa_settings=IPAExtractionSettings(True, True, "_"))

  assert res == [WordEntry(
    graphemes=["a"],
    phonemes=["a"],
    phones=["a"],
  )]


def test_symbols_to_str_with_space():
  res = symbols_to_str_with_space(["a", "b"])
  assert res == "a b"


def test_get_probabilities__empty_list():
  words = []

  res = get_probabilities(words)

  assert len(res) == 0


def test_get_probabilities__ignores_all_same():
  words = [
    WordEntry([], ["a"], ["a"]),
    WordEntry([], ["a"], ["a"]),
  ]

  res = get_probabilities(words)

  assert len(res) == 0


def test_get_probabilities__multiple_phones_are_distinguished():
  words = [
    WordEntry([], ["a"], ["a"]),
    WordEntry([], ["a"], ["a"]),
    WordEntry([], ["a"], ["a"]),
    WordEntry([], ["a"], ["b"]),
    WordEntry([], ["a"], ["b"]),
  ]

  res = get_probabilities(words)

  assert len(res) == 2
  assert res[0] == ("a", "a", 3)
  assert res[1] == ("a", "b", 2)


def test_get_probabilities__rounds_to_six_dec():
  words = [
    WordEntry([], ["a"], ["a"]),
    WordEntry([], ["a"], ["a"]),
    WordEntry([], ["a"], ["a"]),
    WordEntry([], ["a"], ["a"]),
    WordEntry([], ["a"], ["a"]),
    WordEntry([], ["a"], ["b"]),
  ]

  res = get_probabilities(words)

  assert len(res) == 2
  assert res[0] == ("a", "a", 5)
  assert res[1] == ("a", "b", 1)


def test_get_probabilities__sorts_desc_after_probs():
  words = [
    WordEntry([], ["a"], ["a"]),
    WordEntry([], ["a"], ["c"]),
    WordEntry([], ["a"], ["c"]),
    WordEntry([], ["a"], ["c"]),
    WordEntry([], ["a"], ["b"]),
    WordEntry([], ["a"], ["b"]),
  ]

  res = get_probabilities(words)

  assert len(res) == 3
  assert res[0] == ("a", "c", 3)
  assert res[1] == ("a", "b", 2)
  assert res[2] == ("a", "a", 1)


def test_get_probabilities__adds_spaces():
  words = [
    WordEntry([], ["a", "b"], ["a", "c"]),
    WordEntry([], ["a", "b"], ["b", "c"]),
  ]

  res = get_probabilities(words)

  assert len(res) == 2
  assert res[0] == ("a b", "a c", 1)
  assert res[1] == ("a b", "b c", 1)


def test_probabilities_to_df():
  probs = [
    ("a b", "a c", 1),
  ]

  res = probabilities_to_df(probs)

  assert len(res) == 1
  assert list(res.columns) == ["phonemes", "phones", "occurrence"]
  assert list(res.iloc[0]) == ["a b", "a c", 1]


def test_parse_probabilities_df():
  df = DataFrame(
    data=[
      ("a b", "a c", 1),
      ("a b", "a d", 8)
    ],
    columns=["phonemes", "phones", "occurrence"],
  )

  res = parse_probabilities_df(df)

  assert_res = {
    ("a", "b"): [
      (("a", "c"), 1),
      (("a", "d"), 8)
    ]
  }

  assert res == assert_res


def test_replace_with_prob__one_entry():
  symbols = ("a", "b")

  d = {
    ("a", "b"): [
      (("a", "c"), 1),
    ]
  }

  res = replace_with_prob(symbols, d)

  assert res == ("a", "c")


def test_replace_with_prob__respects_probabilities():
  symbols = ("a", "b")
  d = {
    ("a", "b"): [
      (("a", "c"), 1),
      (("a", "d"), 9)
    ]
  }
  res = []

  random.seed(0)
  for _ in range(10000):
    res.append(replace_with_prob(symbols, d))

  amount_of_ac = len([x for x in res if x == ("a", "c")]) / len(res)
  amount_of_ad = len([x for x in res if x == ("a", "d")]) / len(res)

  deviation = 0.005
  assert amount_of_ac + amount_of_ad == 1
  assert 0.1 - deviation <= amount_of_ac <= 0.1 + deviation
  assert 0.9 - deviation <= amount_of_ad <= 0.9 + deviation


def test_check_probabilities_are_valid__probs_equal_one__returns_true():
  d = {
    ("a", "b"): [
      (("a", "c"), 1),
      (("a", "d"), 6)
    ]
  }

  res = check_probabilities_are_valid(d)

  assert res == True


def test_check_probabilities_are_valid__probs_zero__returns_false():
  d = {
    ("a", "b"): [
      (("a", "c"), 0),
    ]
  }

  res = check_probabilities_are_valid(d)

  assert res == False


def test_check_probabilities_are_valid__same_phones_multiple_times():
  d = {
    ("a", "b"): [
      (("a", "c"), 1),
      (("a", "c"), 9),
    ]
  }

  res = check_probabilities_are_valid(d)

  assert res == False
