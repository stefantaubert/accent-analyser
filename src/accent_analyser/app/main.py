from logging import Logger, getLogger
from pathlib import Path
from typing import Dict, List, Tuple

import pandas as pd
from accent_analyser.core.rule_detectionv2 import (df_to_data,
                                                   get_phone_occurrences,
                                                   get_phoneme_occurrences,
                                                   get_rules_from_words)
from accent_analyser.core.rule_stats import get_rule_stats, rule_stats_to_df
from accent_analyser.core.word_probabilities import (get_probabilities,
                                                     parse_probabilities_df,
                                                     probabilities_to_df)
from accent_analyser.core.word_stats import get_word_stats, word_stats_to_df
from text_utils.ipa2symb import IPAExtractionSettings


def load_probabilities(path: Path) -> Dict[Tuple[str, ...], List[Tuple[Tuple[str, ...], float]]]:
  df = pd.read_csv(path, sep="\t")
  res = parse_probabilities_df(df)
  return res


def print_info(paths: List[Path]):
  logger = getLogger(__name__)

  ipa_settings = IPAExtractionSettings(
    ignore_arcs=True,
    ignore_tones=True,
    replace_unknown_ipa_by="_",
  )

  merged_df = None
  for path in paths:
    if not path.exists():
      logger.error("Path does not exist!")
      return
    df = pd.read_csv(path, sep="\t", na_filter=False)
    if merged_df is None:
      merged_df = df
    else:
      merged_df = pd.concat([merged_df, df])

  words = df_to_data(merged_df, ipa_settings=ipa_settings)
  word_probs = get_probabilities(words)
  word_probs_df = probabilities_to_df(word_probs)

  output_path = Path("out/word_probs.csv")
  output_path.parent.mkdir(parents=False, exist_ok=True)
  word_probs_df.to_csv(output_path, sep="\t", header=True, index=False)

  phoneme_occurrences = get_phoneme_occurrences(words)
  phone_occurrences = get_phone_occurrences(words)

  word_rules = get_rules_from_words(words)
  word_stats = get_word_stats(word_rules, phone_occurrences, phoneme_occurrences)
  word_stats_df = word_stats_to_df(word_stats)

  output_path = Path("out/res_word_stats.csv")
  output_path.parent.mkdir(parents=False, exist_ok=True)
  word_stats_df.to_csv(output_path, sep="\t", header=True, index=False)

  rule_stats = get_rule_stats(word_rules, phone_occurrences, phoneme_occurrences)
  rule_stats_df = rule_stats_to_df(rule_stats)

  output_path = Path("out/res_rule_stats.csv")
  output_path.parent.mkdir(parents=False, exist_ok=True)
  rule_stats_df.to_csv(output_path, sep="\t", header=True, index=False)
