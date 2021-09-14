import random
from collections import OrderedDict

from accent_analyser.core.rule_detection import WordEntry
from accent_analyser.core.word_probabilities import (
    check_probabilities_are_valid, get_probabilities, parse_probabilities_df,
    probabilities_to_df, replace_with_prob, symbols_to_str_with_space)
from pandas import DataFrame


def test_symbols_to_str_with_space():
  res = symbols_to_str_with_space(("a", "b"))
  assert res == "a b"

# region get_probabilities


def test_get_probabilities__empty_list():
  res = get_probabilities(phone_occurrences=OrderedDict(), phoneme_occurrences=OrderedDict())

  assert len(res) == 0


def test_get_probabilities__ignores_all_same():
  word1 = WordEntry(
    graphemes=("a",),
    phonemes=("b",),
    phones=("c",),
  )

  phone_occurrences = OrderedDict({
    word1: 4,
  })

  phoneme_occurrences = OrderedDict({
    (word1.graphemes, word1.phonemes): 4,
  })

  res = get_probabilities(phone_occurrences, phoneme_occurrences)

  assert len(res) == 0


def test_get_probabilities__multiple_phones_are_distinguished():
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

  phone_occurrences = OrderedDict({
    word1: 4,
    word2: 3,
  })

  phoneme_occurrences = OrderedDict({
    (("a",), ("b",)): 7,
  })

  res = get_probabilities(phone_occurrences, phoneme_occurrences)

  assert len(res) == 2
  assert res[0] == ("b", "c", 4)
  assert res[1] == ("b", "d", 3)


def test_get_probabilities__sorts_desc_after_probs():
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

  word3 = WordEntry(
    graphemes=("a",),
    phonemes=("b",),
    phones=("e",),
  )

  phone_occurrences = OrderedDict({
    word1: 3,
    word2: 1,
    word3: 2,
  })

  phoneme_occurrences = OrderedDict({
    (("a",), ("b",)): 6,
  })

  res = get_probabilities(phone_occurrences, phoneme_occurrences)

  assert len(res) == 3
  assert res[0] == ("b", "c", 3)
  assert res[1] == ("b", "e", 2)
  assert res[2] == ("b", "d", 1)


def test_get_probabilities__adds_spaces():
  word1 = WordEntry(
    graphemes=("a",),
    phonemes=("b", "c",),
    phones=("c", "d",),
  )

  phone_occurrences = OrderedDict({
    word1: 3,
  })

  phoneme_occurrences = OrderedDict({
    (word1.graphemes, word1.phonemes): 4,
  })

  res = get_probabilities(phone_occurrences, phoneme_occurrences)

  assert len(res) == 1
  assert res[0] == ("b c", "c d", 3)

# endregion


def test_probabilities_to_df():
  probabilities = [
    ("a b", "a c", 1),
  ]

  res = probabilities_to_df(probabilities)

  assert len(res) == 1
  assert list(res.columns) == ["Phonemes", "Phones", "Occurrence"]
  assert list(res.iloc[0]) == ["a b", "a c", 1]


def test_parse_probabilities_df():
  df = DataFrame(
    data=[
      ("a b", "a c", 1),
      ("a b", "a d", 8)
    ],
    columns=["Phonemes", "Phones", "Occurrence"],
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
      (("a", "d"), 6),
    ],
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
