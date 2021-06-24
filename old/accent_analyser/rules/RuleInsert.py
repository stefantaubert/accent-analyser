from accent_analyser.rules.IpaRule import IpaRule


class RuleInsert(IpaRule):
  def __init__(self, likelihood=1.0):
    super().__init__(likelihood)

  def _convert_core(self, words: list, current_index: int):
    word = words[current_index].content
    if word == "ənd":
      return "əndə"
    elif word == "vɪlɪdʒ":
      return "vɪlɪdʒi"
    else:
      return word
