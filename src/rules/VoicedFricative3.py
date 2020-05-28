from src.rules.IpaRule import IpaRule

def replace(word: str):
  return word.replace("θ", "s")

class VoicedFricative3(IpaRule):
  def __init__(self, likelihood=0.71):
    super().__init__(likelihood)
    self.name = "Voiced Fricative: [s] instead of /θ/"

  def _convert_core(self, words: list, current_index: int):
    word = words[current_index].content
    word = replace(word)
    return word
  