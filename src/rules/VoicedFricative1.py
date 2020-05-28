from src.rules.IpaRule import IpaRule

def replace(word: str):
  return word.replace("v", "w")

class VoicedFricative1(IpaRule):
  def __init__(self, likelihood=0.51):
    super().__init__(likelihood)
    self.name = "Voiced Fricative: [w] instead of /v/"

  def _convert_core(self, words: list, current_index: int):
    word = words[current_index].content
    word = replace(word)
    return word
  