from accent_analyser.rules.IpaRule import IpaRule


def replace(word: str):
  return word.replace("ʒ", "ɹ")


class VoicedFricative2(IpaRule):
  def __init__(self, likelihood=0.5):
    super().__init__(likelihood)
    self.name = "Voiced Fricative: [ɹ] instead of /ʒ/"

  def _convert_core(self, words: list, current_index: int):
    word = words[current_index].content
    word = replace(word)
    return word
