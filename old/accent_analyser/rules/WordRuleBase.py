from accent_analyser.rules.RuleBase import RuleBase


class WordRuleBase(RuleBase):
  def __init__(self, likelihood=1.0):
    super().__init__(likelihood)

  def convert(self, words: list, current_index: int):
    if self.should_convert():
      return self._convert_core(words, current_index)
    else:
      return words[current_index].content

  def _convert_core(self, words: list, current_index: int):
    raise Exception()
