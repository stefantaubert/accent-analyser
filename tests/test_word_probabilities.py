import random

from accent_analyser.core.rule_detectionv2 import WordEntry
from accent_analyser.core.word_probabilities import (
    check_probabilities_are_valid, get_probabilities, parse_probabilities_df,
    probabilities_to_df, replace_with_prob, symbols_to_str_with_space)
from pandas import DataFrame


def test_symbols_to_str_with_space():
  res = symbols_to_str_with_space(["a", "b"])
  assert res == "a b"


def test_get_probabilities__empty_list():
  words = []

  res = get_probabilities(words)

  assert len(res) == 0


def test_get_probabilities__ignores_all_same():
  words = [
    WordEntry((), ("a"), ("a")),
    WordEntry((), ("a"), ("a")),
  ]

  res = get_probabilities(words)

  assert len(res) == 0


def test_get_probabilities__multiple_phones_are_distinguished():
  words = [
    WordEntry((), ("a"), ("a")),
    WordEntry((), ("a"), ("a")),
    WordEntry((), ("a"), ("a")),
    WordEntry((), ("a"), ("b")),
    WordEntry((), ("a"), ("b")),
  ]

  res = get_probabilities(words)

  assert len(res) == 2
  assert res[0] == ("a", "a", 3)
  assert res[1] == ("a", "b", 2)


def test_get_probabilities__rounds_to_six_dec():
  words = [
    WordEntry((), ("a"), ("a")),
    WordEntry((), ("a"), ("a")),
    WordEntry((), ("a"), ("a")),
    WordEntry((), ("a"), ("a")),
    WordEntry((), ("a"), ("a")),
    WordEntry((), ("a"), ("b")),
  ]

  res = get_probabilities(words)

  assert len(res) == 2
  assert res[0] == ("a", "a", 5)
  assert res[1] == ("a", "b", 1)


def test_get_probabilities__sorts_desc_after_probs():
  words = [
    WordEntry((), ("a"), ("a")),
    WordEntry((), ("a"), ("c")),
    WordEntry((), ("a"), ("c")),
    WordEntry((), ("a"), ("c")),
    WordEntry((), ("a"), ("b")),
    WordEntry((), ("a"), ("b")),
  ]

  res = get_probabilities(words)

  assert len(res) == 3
  assert res[0] == ("a", "c", 3)
  assert res[1] == ("a", "b", 2)
  assert res[2] == ("a", "a", 1)


def test_get_probabilities__adds_spaces():
  words = [
    WordEntry((), ("a", "b"), ("a", "c")),
    WordEntry((), ("a", "b"), ("b", "c")),
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
