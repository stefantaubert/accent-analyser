from src.rules.IpaRule import IpaRule

class RuleSubstitue2(IpaRule):
  def __init__(self, likelihood=1.0):
    super().__init__(likelihood)
    
  def _convert_core(self, words: list, current_index: int):
    word = words[current_index].content
    if word == "ðer":
      return "ser"
    elif word == "ðɪs":
      return "sɪs"
    else:
      return word