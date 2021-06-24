from accent_analyser.InputWord import InputWord
from accent_analyser.rules.EngRule import EngRule
from accent_analyser.rules.IpaRule import IpaRule
from accent_analyser.rules.SentenceRule import SentenceRule


def get_relevant_rules(all_rules: list, t: type):
  relevant_rules = [r for r in all_rules if isinstance(r, t)]
  return relevant_rules


class InputWordList():
  def __init__(self, sentence):
    super().__init__()
    self.sentence = sentence
    self._extract_words()

  def _extract_words(self):
    tokens = self.sentence.split(' ')
    self.input_words = [InputWord(token) for token in tokens]

  def transform_sentence(self, rules):
    relev_rules = get_relevant_rules(rules, SentenceRule)
    for rule in relev_rules:
      self.input_words = rule.convert(self.input_words)
      # todo maybe insert special chars of end to end of last word und start to start of next word

  def transform_words(self, rules):
    relev_rules = get_relevant_rules(rules, EngRule)
    for rule in relev_rules:
      for i, w in enumerate(self.input_words):
        result = rule.convert(self.input_words, i)
        w.update(result)

  def convert_to_ipa(self):
    for w in self.input_words:
      w.convert_to_ipa()

  def transform_ipa(self, rules):
    relev_rules = get_relevant_rules(rules, IpaRule)
    for rule in relev_rules:
      for i, w in enumerate(self.input_words):
        result = rule.convert(self.input_words, i)
        w.update(result)

  def get_result(self):
    result = [word.get_result() for word in self.input_words if not word.is_empty()]
    return result

  def transform(self, rules):
    self.transform_sentence(rules)
    self.transform_words(rules)
    self.convert_to_ipa()
    self.transform_ipa(rules)
    result = self.get_result()
    result_str = ' '.join(result)
    return result_str
