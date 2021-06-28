
from logging import Logger, getLogger
from pathlib import Path
from typing import List

import pandas as pd
from accent_analyser.core.rule_detection import df_to_data, parse_eng_data
from text_utils.ipa2symb import IPAExtractionSettings


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

  out_df = parse_eng_data(words)
  output_path = Path("out/res.csv")
  output_path.parent.mkdir(parents=False, exist_ok=True)
  out_df.to_csv(output_path, sep="\t", header=True)
