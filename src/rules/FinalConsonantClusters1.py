from src.rules.IpaRule import IpaRule

def replace(word: str):
  if word.endswith('st'):
    return word[:-1]
  else:
    return word
  
class FinalConsonantClusters1(IpaRule):
  def __init__(self, likelihood=0.79):
    super().__init__(likelihood)
    self.name = "Voiced Fricative: [s] instead of /st/"

  def _convert_core(self, words: list, current_index: int):
    word = words[current_index].content
    word = replace(word)
    return word
  
if __name__ == "__main__":
  print(replace("first"))