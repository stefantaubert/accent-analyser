
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
