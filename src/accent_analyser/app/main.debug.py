from pathlib import Path

from app.main import print_info

if __name__ == "__main__":
  print_info(paths=[
    Path("/home/mi/data/textgrid-tools/200928-002/6_words_ipa_phones.csv"),
    Path("/home/mi/data/textgrid-tools/200928-003/6_words_ipa_phones.csv"),
    Path("/home/mi/data/textgrid-tools/200928-004/6_words_ipa_phones.csv"),
  ])