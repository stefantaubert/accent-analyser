from accent_analyser.rules.WordRuleBase import WordRuleBase


class EngRule(WordRuleBase):
  def __init__(self, likelihood=1.0):
    super().__init__(likelihood)
