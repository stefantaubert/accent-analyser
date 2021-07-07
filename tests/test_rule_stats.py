

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
