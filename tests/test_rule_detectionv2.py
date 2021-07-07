from collections import OrderedDict

from accent_analyser.core.rule_detectionv2 import (UNCHANGED_RULE, Change,
                                                   ChangeType, Rule, RuleType,
                                                   WordEntry,
                                                   changes_cluster_to_rule,
                                                   cluster_changes,
                                                   clustered_changes_to_rules,
                                                   df_to_data, get_ndiff_info,
                                                   get_phone_occurrences,
                                                   get_phoneme_occurrences,
                                                   get_rules_from_words,
                                                   positions_to_str,
                                                   rule_to_str, rules_to_str)
from ordered_set import OrderedSet
from pandas.core.frame import DataFrame
from text_utils import Language
from text_utils.ipa2symb import IPAExtractionSettings


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

# region clustered_changes_to_rules


def test_clustered_changes_to_rules__two_changes():
  insertion_change = OrderedDict({
    0: Change("a", ChangeType.ADD),
  })

  omission_change = OrderedDict({
    1: Change("a", ChangeType.REMOVE),
  })

  res = clustered_changes_to_rules([insertion_change, omission_change])

  assert len(res) == 2
  assert res[(0,)].rule_type == RuleType.INSERTION
  assert res[(0,)].from_symbols == ()
  assert res[(0,)].to_symbols == ("a",)

  assert res[(1,)].rule_type == RuleType.OMISSION
  assert res[(1,)].from_symbols == ("a",)
  assert res[(1,)].to_symbols == ()


def test_clustered_changes_to_rules__sorts_after_positions():
  change1 = OrderedDict({
    0: Change("a", ChangeType.ADD),
  })

  change2 = OrderedDict({
    1: Change("b", ChangeType.ADD),
  })

  change3 = OrderedDict({
    2: Change("c", ChangeType.ADD),
    3: Change("d", ChangeType.REMOVE),
  })

  res = clustered_changes_to_rules([change2, change1, change3])

  assert len(res) == 3
  assert list(res.keys()) == [(0,), (1,), (2,)]
  assert res[(0,)].to_symbols == ("a",)
  assert res[(1,)].to_symbols == ("b",)
  assert res[(2,)].to_symbols == ("c",)


# endregion


# region rules_to_str


def test_rules_to_str__empty_dict__returns_constant():
  res = rules_to_str(OrderedDict())

  assert res == UNCHANGED_RULE


def test_rules_to_str__one_entry():
  r = Rule(
    rule_type=RuleType.OMISSION,
    from_symbols=("a", "b",),
    to_symbols=(),
  )

  word_rule = OrderedDict({
    (0,): r,
  })

  res = rules_to_str(word_rule)

  assert res == "O(ab;0)"


def test_rules_to_str__two_entries__are_separated_by_comma():
  r = Rule(
    rule_type=RuleType.OMISSION,
    from_symbols=("a", "b",),
    to_symbols=(),
  )

  word_rule = OrderedDict({
    (0,): r,
    (1,): r,
  })

  res = rules_to_str(word_rule)

  assert res == "O(ab;0), O(ab;1)"


def test_rules_to_str__entries__are_in_same_positions_as_in_list():
  r = Rule(
    rule_type=RuleType.OMISSION,
    from_symbols=("a", "b",),
    to_symbols=(),
  )

  word_rule = OrderedDict({
    (2,): r,
    (1,): r,
    (3,): r,
  })

  res = rules_to_str(word_rule)

  assert res == "O(ab;2), O(ab;1), O(ab;3)"

# endregion

# region rule_to_str


def test_rule_to_str__none_rule__returns_constant():
  res = rule_to_str(None, None)

  assert res == UNCHANGED_RULE


def test_rule_to_str__omission_with_pos():
  r = Rule(
    rule_type=RuleType.OMISSION,
    from_symbols=("a", "b",),
    to_symbols=(),
  )

  res = rule_to_str(r, positions=(0,))

  assert res == "O(ab;0)"


def test_rule_to_str__omission_without_pos():
  r = Rule(
    rule_type=RuleType.OMISSION,
    from_symbols=("a", "b",),
    to_symbols=(),
  )

  res = rule_to_str(r, positions=None)

  assert res == "O(ab)"


def test_rule_to_str__insertion_with_pos():
  r = Rule(
    rule_type=RuleType.INSERTION,
    from_symbols=(),
    to_symbols=("a", "b",),
  )

  res = rule_to_str(r, positions=(0,))

  assert res == "I(ab;0)"


def test_rule_to_str__insertion_without_pos():
  r = Rule(
    rule_type=RuleType.INSERTION,
    from_symbols=(),
    to_symbols=("a", "b",),
  )

  res = rule_to_str(r, positions=None)

  assert res == "I(ab)"


def test_rule_to_str__substitution_with_pos():
  r = Rule(
    rule_type=RuleType.SUBSTITUTION,
    from_symbols=("c"),
    to_symbols=("a", "b",),
  )

  res = rule_to_str(r, positions=(0,))

  assert res == "S(c;ab;0)"


def test_rule_to_str__substitution_without_pos():
  r = Rule(
    rule_type=RuleType.SUBSTITUTION,
    from_symbols=("c"),
    to_symbols=("a", "b",),
  )

  res = rule_to_str(r, positions=None)

  assert res == "S(c;ab)"

# endregion

# region positions_to_str


def test_positions_to_str__empty_list():
  res = positions_to_str([])

  assert res == ""


def test_positions_to_str__one_entry():
  res = positions_to_str([1])

  assert res == "1"


def test_positions_to_str__two_entries():
  res = positions_to_str([1, 2])

  assert res == "1,2"


def test_positions_to_str__three_entries():
  res = positions_to_str([1, 2, 3])

  assert res == "1-3"


# endregion

# region get_phone_occurrences


def test_get_phone_occurrences__no_words__return_empty_dict():
  res = get_phone_occurrences([])

  assert len(res) == 0


def test_get_phone_occurrences__one_word__return_one():
  word1 = WordEntry(
    graphemes=("a",),
    phonemes=("a",),
    phones=("a",),
  )

  res = get_phone_occurrences([word1])

  assert len(res) == 1
  assert res[word1] == 1


def test_get_phone_occurrences__two_same_words__return_two():
  word1 = WordEntry(
    graphemes=("a",),
    phonemes=("a",),
    phones=("a",),
  )

  res = get_phone_occurrences([word1, word1])

  assert len(res) == 1
  assert res[word1] == 2


def test_get_phone_occurrences__two_different_words__return_one_for_each():
  word1 = WordEntry(
    graphemes=("a",),
    phonemes=("a",),
    phones=("a",),
  )
  word2 = WordEntry(
    graphemes=("a",),
    phonemes=("a",),
    phones=("b",),
  )

  res = get_phone_occurrences([word1, word2])

  assert len(res) == 2
  assert res[word1] == 1
  assert res[word2] == 1


# endregion

# region get_phoneme_occurrences


def test_get_phoneme_occurrences__no_words__return_empty_dict():
  res = get_phoneme_occurrences([])

  assert len(res) == 0


def test_get_phoneme_occurrences__one_word__return_one():
  word1 = WordEntry(
    graphemes=("a",),
    phonemes=("b",),
    phones=("c",),
  )

  res = get_phoneme_occurrences([word1])

  assert len(res) == 1
  assert res[(("a",), ("b",))] == 1


def test_get_phoneme_occurrences__two_same_words__return_two():
  word1 = WordEntry(
    graphemes=("a",),
    phonemes=("b",),
    phones=("c",),
  )

  res = get_phoneme_occurrences([word1, word1])

  assert len(res) == 1
  assert res[(("a",), ("b",))] == 2


def test_get_phoneme_occurrences__two_different_phones__return_two():
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

  res = get_phoneme_occurrences([word1, word2])

  assert len(res) == 1
  assert res[(("a",), ("b",))] == 2


def test_get_phoneme_occurrences__two_different_phonemes__return_one_for_each():
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

  res = get_phoneme_occurrences([word1, word2])

  assert len(res) == 2
  assert res[(("a",), ("b",))] == 1
  assert res[(("a",), ("c",))] == 1


# endregion

# region get_rules_from_words


def test_get_rules__one_word__nothing():
  word1 = WordEntry(
      graphemes=("a",),
      phonemes=("a",),
      phones=("a",),
    )

  res = get_rules_from_words(OrderedSet([word1]))

  assert len(res) == 1
  assert len(res[word1]) == 0


def test_get_rules__one_word():
  word1 = WordEntry(
      graphemes=("a",),
      phonemes=("a",),
      phones=("b",),
    )

  res = get_rules_from_words(OrderedSet([word1]))

  assert len(res) == 1
  assert len(res[word1]) == 1
  assert res[word1][(0,)].rule_type == RuleType.SUBSTITUTION
  assert res[word1][(0,)].from_symbols == ("a",)
  assert res[word1][(0,)].to_symbols == ("b",)


def test_get_rules__two_words():
  word1 = WordEntry(
      graphemes=("a",),
      phonemes=("a",),
      phones=("b",),
    )

  word2 = WordEntry(
      graphemes=("a",),
      phonemes=("a",),
      phones=("c",),
    )

  res = get_rules_from_words(OrderedSet([word1, word2]))

  assert len(res) == 2
  assert len(res[word1]) == 1
  assert res[word1][(0,)].rule_type == RuleType.SUBSTITUTION
  assert res[word1][(0,)].from_symbols == ("a",)
  assert res[word1][(0,)].to_symbols == ("b",)
  assert len(res[word2]) == 1
  assert res[word2][(0,)].rule_type == RuleType.SUBSTITUTION
  assert res[word2][(0,)].from_symbols == ("a",)
  assert res[word2][(0,)].to_symbols == ("c",)

# endregion
