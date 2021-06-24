
from logging import Logger, getLogger
from pathlib import Path

import pandas as pd
from core.rule_detection import df_to_data, parse_eng_data
from text_utils.ipa2symb import IPAExtractionSettings


def print_info(path: Path):
  logger = getLogger(__name__)

  if not path.exists():
    logger.error("Path does not exist!")
    return

  df = pd.read_csv(path, sep="\t", na_filter= False)
  ipa_settings = IPAExtractionSettings(
    ignore_arcs=True,
    ignore_tones=True,
    replace_unknown_ipa_by="_",
  )

  words = df_to_data(df, ipa_settings=ipa_settings)

  parse_eng_data(words)
