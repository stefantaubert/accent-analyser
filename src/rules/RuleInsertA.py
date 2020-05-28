from src.InputWord import InputWord
from src.rules.SentenceRule import SentenceRule


class RuleInsertA(SentenceRule):
  def __init__(self, likelihood=1.0):
    super().__init__(likelihood)

  def _convert_core(self, words: list):
    result = []
    for w in words:
      if w.content == 'test':
        word_a = InputWord('a')
        result.append(word_a)
      result.append(w)
    return result
