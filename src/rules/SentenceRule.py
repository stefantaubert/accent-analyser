from src.rules.RuleBase import RuleBase

class SentenceRule(RuleBase):
  def __init__(self, likelihood=1.0):
    super().__init__(likelihood)

  def convert(self, words: list) -> list:
    if self.should_convert():
      return self._convert_core(words)
    else:
      return words