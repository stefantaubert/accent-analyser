from collections import OrderedDict

from accent_analyser.core.rule_detectionv2 import (Change, ChangeType, Rule,
                                                   RuleType, WordEntry,
                                                   changes_cluster_to_rule,
                                                   cluster_changes, df_to_data,
                                                   get_indicies_as_str,
                                                   get_ndiff_info,
                                                   get_rules_from_words)
from ordered_set import OrderedSet
from pandas.core.frame import DataFrame
from text_utils import Language
from text_utils.ipa2symb import IPAExtractionSettings

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

# region get_indicies_as_str


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
# endregion


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
