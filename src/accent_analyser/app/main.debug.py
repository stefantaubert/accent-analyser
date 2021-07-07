from pathlib import Path

from accent_analyser.app.main import load_probabilities, print_info
from accent_analyser.core.word_probabilities import replace_with_prob

if __name__ == "__main__":
  print_info(paths=[
    Path("/home/mi/data/textgrid-tools/200928-002/6_words_ipa_phones.csv"),
    Path("/home/mi/data/textgrid-tools/200928-003/6_words_ipa_phones.csv"),
    Path("/home/mi/data/textgrid-tools/200928-004/6_words_ipa_phones.csv"),
  ])

  output_path = Path("out/word_probs.csv")

  mapping_table = load_probabilities(output_path)

  res = replace_with_prob(("a",), mapping_table)
