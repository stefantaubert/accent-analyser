from accent_analyser.rules.EngRule import EngRule


class RuleHeShe(EngRule):
  def __init__(self, likelihood=1.0):
    super().__init__(likelihood)

  def _convert_core(self, words: list, current_index: int):
    word = words[current_index].content
    if word == "he":
      return "she"
    elif word == "she":
      return "he"
    else:
      return word
