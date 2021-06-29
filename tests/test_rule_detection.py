from collections import OrderedDict

from accent_analyser.core.rule_detection import (Change, ChangeType, Rule,
                                                 RuleType, WordEntry,
                                                 changes_cluster_to_rule,
                                                 cluster_changes,
                                                 get_ndiff_info, get_rules,
                                                 get_word_stats,
                                                 sort_rules_after_positions,
                                                 sort_word_stats_df,
                                                 word_stats_to_df)


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


def test_rule_is_nothing_by_default():
  res = Rule()

  assert res == Rule(
    rule_type=RuleType.NOTHING,
    from_symbols=[],
    to_symbols=[],
    positions=[],
  )


def test_changes_cluster_to_rule__omission():
  changes = OrderedDict({
    0: Change("a", ChangeType.REMOVE),
  })

  res = changes_cluster_to_rule(changes)

  assert res == Rule(
    rule_type=RuleType.OMISSION,
    from_symbols=["a"],
    to_symbols=[],
    positions=[0],
  )


def test_changes_cluster_to_rule__insertion():
  changes = OrderedDict({
    0: Change("a", ChangeType.ADD),
  })

  res = changes_cluster_to_rule(changes)

  assert res == Rule(
    rule_type=RuleType.INSERTION,
    from_symbols=[],
    to_symbols=["a"],
    positions=[0],
  )


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

  res = changes_cluster_to_rule(changes)

  assert_res = Rule(
    rule_type=RuleType.SUBSTITUTION,
    from_symbols=["a", "b"],
    to_symbols=["c"],
    positions=[0, 1],
  )

  assert res.rule_type == assert_res.rule_type
  assert res.from_symbols == assert_res.from_symbols
  assert res.to_symbols == assert_res.to_symbols
  assert res.positions == assert_res.positions


def test_changes_cluster_to_rule__substitution_remove_add():
  #from_w = ['h', 'ˈ', 'a', 'ʊ']
  #to_w =['x', 'ˈ', 'a', 'ʊ']
  changes = OrderedDict({
    0: Change("a", ChangeType.REMOVE),
    1: Change("b", ChangeType.ADD),
  })

  res = changes_cluster_to_rule(changes)

  assert_res = Rule(
    rule_type=RuleType.SUBSTITUTION,
    from_symbols=["a"],
    to_symbols=["b"],
    positions=[0],
  )

  assert res.rule_type == assert_res.rule_type
  assert res.from_symbols == assert_res.from_symbols
  assert res.to_symbols == assert_res.to_symbols
  assert res.positions == assert_res.positions


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
  assert list(res.columns) == ["Word", "English", "Phonemes", "Phones", "Rules",
                               "Occurrences", "Occurrences Total", "Occurrences (%)"]
  assert list(res.iloc[0]) == [1, 'a', 'b', 'c', 'I(a;0)', 3, 4, '75.00']


def test_sort_word_stats_df():
  resulting_csv_data = [
    (1, "a", "b", "a", "ruleB", 1, 4, "75.00"),
    (1, "a", "b", "a", "ruleC", 2, 4, "75.00"),
    (1, "a", "b", "a", "ruleA", 1, 4, "75.00"),
    (0, "a", "a", "a", "rule1", 1, 4, "75.00"),
  ]

  sort_word_stats_df(resulting_csv_data)

  assert len(resulting_csv_data) == 4
  assert resulting_csv_data[0] == (0, "a", "a", "a", "rule1", 1, 4, "75.00")
  assert resulting_csv_data[1] == (1, "a", "b", "a", "ruleC", 2, 4, "75.00")
  assert resulting_csv_data[2] == (1, "a", "b", "a", "ruleA", 1, 4, "75.00")
  assert resulting_csv_data[3] == (1, "a", "b", "a", "ruleB", 1, 4, "75.00")


def test_sort_rules_after_positions():
  r1 = Rule(from_symbols=["a"], positions=[0])
  r2 = Rule(from_symbols=["a"], positions=[0, 1])
  r3 = Rule(from_symbols=["a"], positions=[1, 2])
  r4 = Rule(from_symbols=["a"], positions=[4])
  rules = (r4, r2, r3, r1)

  res = sort_rules_after_positions(rules)

  assert res == (r1, r2, r3, r4)
