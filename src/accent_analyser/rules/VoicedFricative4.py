from accent_analyser.rules.IpaRule import IpaRule


def replace(word: str):
  return word.replace("ð", "d")


class VoicedFricative4(IpaRule):
  def __init__(self, likelihood=0.79):
    super().__init__(likelihood)
    self.name = "Voiced Fricative: [d] instead of /ð/"

  def _convert_core(self, words: list, current_index: int):
    word = words[current_index].content
    word = replace(word)
    return word
