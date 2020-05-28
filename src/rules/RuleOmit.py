from src.rules.IpaRule import IpaRule

class RuleOmit(IpaRule):
  def __init__(self, likelihood=1.0):
    super().__init__(likelihood)

  def _convert_core(self, words: list, current_index: int):
    word = words[current_index].content
    if word == "fɪst":
      return "fɪs"
    elif word == "fɔːrɪst":
      return "fɔːrɪs"
    elif word == "wʊlf":
      return "wʊf"
    else:
      return word
