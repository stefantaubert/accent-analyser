from src.rules.EngRule import EngRule

class RuleRemoveThe(EngRule):
  def __init__(self, likelihood=1.0):
    super().__init__(likelihood)

  def _convert_core(self, words: list, current_index: int):
    word = words[current_index].content
    if word == "the":
      return ""
    else:
      return word
