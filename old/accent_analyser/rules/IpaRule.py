from accent_analyser.rules.WordRuleBase import WordRuleBase


class IpaRule(WordRuleBase):
  def __init__(self, likelihood=1.0):
    super().__init__(likelihood)

  def _convert_core(self, words: list):
    raise Exception()
