from logging import Logger, getLogger
from pathlib import Path
from typing import Dict, List, Tuple

import pandas as pd
from accent_analyser.core.rule_detection import (df_to_data,
                                                 get_phone_occurrences,
                                                 get_phoneme_occurrences,
                                                 get_rules_from_words)
from accent_analyser.core.rule_stats import get_rule_stats, rule_stats_to_df
from accent_analyser.core.word_probabilities import (ProbabilitiesDict,
                                                     get_probabilities,
                                                     parse_probabilities_df,
                                                     probabilities_to_df)
from accent_analyser.core.word_stats import get_word_stats, word_stats_to_df


def load_probabilities(path: Path) -> ProbabilitiesDict:
  df = pd.read_csv(path, sep="\t")
  res = parse_probabilities_df(df)
  return res


def print_info(paths: List[Path]):
  logger = getLogger(__name__)

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

  words = df_to_data(merged_df)

  phoneme_occurrences = get_phoneme_occurrences(words)
  phone_occurrences = get_phone_occurrences(words)

  word_probs = get_probabilities(phone_occurrences, phoneme_occurrences)
  word_probs_df = probabilities_to_df(word_probs)

  output_path = Path("out/word_probs.csv")
  output_path.parent.mkdir(parents=False, exist_ok=True)
  word_probs_df.to_csv(output_path, sep="\t", header=True, index=False)

  word_rules = get_rules_from_words(words)
  word_stats = get_word_stats(word_rules, phone_occurrences, phoneme_occurrences)
  word_stats_df = word_stats_to_df(word_stats)

  output_path = Path("out/res_word_stats.csv")
  output_path.parent.mkdir(parents=False, exist_ok=True)
  word_stats_df.to_csv(output_path, sep="\t", header=True, index=False)

  rule_stats = get_rule_stats(word_rules, phone_occurrences)
  rule_stats_df = rule_stats_to_df(rule_stats)

  output_path = Path("out/res_rule_stats.csv")
  output_path.parent.mkdir(parents=False, exist_ok=True)
  rule_stats_df.to_csv(output_path, sep="\t", header=True, index=False)
