from accent_analyser.core.cluster_rules import *


def test_get_vector():
  rule_occurences = {"a": 1 / 2, "c": 1 / 4, "d": 1 / 4}
  all_rules = ["a", "b", "c", "d", "e"]
  res = get_vector(rule_occurences, all_rules)

  assert all(res == np.array([1 / 2, 0, 1 / 4, 1 / 4, 0]))


def test_get_fingerprint():
  speaker_word_rules: OrderedDictType = {("a", "aah"): "rule1", ("b", "beh"): "rule2", ("c", "zeh"): "rule1"}
