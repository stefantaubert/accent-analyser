from collections import OrderedDict
from logging import getLogger
from pathlib import Path
from typing import List

import pandas as pd
from accent_analyser.core.cluster_rules import (cluster_fingerprints,
                                                cluster_fingerprints_kmeans,
                                                compare_all_fingerprints,
                                                get_fingerprint)
from accent_analyser.core.rule_detection import (df_to_data,
                                                 get_phone_occurrences,
                                                 get_phoneme_occurrences,
                                                 get_rules_from_words)
from text_utils.ipa2symb import IPAExtractionSettings


def main(speaker_paths: List[Path]):
  logger = getLogger(__name__)

  ipa_settings = IPAExtractionSettings(
    ignore_arcs=True,
    ignore_tones=True,
    replace_unknown_ipa_by="_",
  )

  all_dfs = []

  for speaker_path in speaker_paths:
    if not speaker_path.exists():
      logger.error("Path does not exist!")
      return
    speaker_df = pd.read_csv(speaker_path, sep="\t", na_filter=False)
    all_dfs.append(speaker_df)

  speaker_words = {i: df_to_data(speaker_df, ipa_settings=ipa_settings)
                   for i, speaker_df in enumerate(all_dfs)}

  all_rules = set()
  for speaker_id, speaker_word in speaker_words.items():
    speaker_word_rules = get_rules_from_words(speaker_word)
    all_rules |= {x for y in speaker_word_rules.values() for x in y.values()}

  speaker_fingerprints = OrderedDict()
  for speaker_id, speaker_word in speaker_words.items():
    speaker_phoneme_occurrences = get_phoneme_occurrences(speaker_word)
    speaker_phone_occurrences = get_phone_occurrences(speaker_word)
    speaker_word_rules = get_rules_from_words(speaker_word)

    speaker_fingerprint = get_fingerprint(speaker_word_rules, speaker_phone_occurrences,
                                          speaker_phoneme_occurrences, all_rules)
    speaker_fingerprints[speaker_id] = speaker_fingerprint

  labels = ["2_1", "2_2", "2_3", "2_4", "3_1", "3_2", "3_3"]
  #cluster = cluster_fingerprints(list(speaker_fingerprints.values()), labels)
  #logger.info("Speaker similarities: ...")

  #print(compare_all_fingerprints(list(speaker_fingerprints.values()), labels))

  cluster_fingerprints_kmeans(list(speaker_fingerprints.values()), 2, labels)


if __name__ == "__main__":
  main(speaker_paths=[
    Path("in/002_1.csv"),
    Path("in/002_2.csv"),
    Path("in/002_3.csv"),
    Path("in/002_4.csv"),
    Path("in/003_1.csv"),
    Path("in/003_2.csv"),
    Path("in/003_3.csv"),
  ])
