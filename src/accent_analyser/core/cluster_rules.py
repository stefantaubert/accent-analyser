from collections import OrderedDict
from typing import Any, List, Optional
from typing import OrderedDict as OrderedDictType
from typing import Set, Tuple

from accent_analyser.core.rule_detection import (PhonemeOccurrences,
                                                 PhoneOccurrences, Rule,
                                                 RuleType, WordEntry,
                                                 WordRules, rule_to_str,
                                                 rules_to_str)
from accent_analyser.core.rule_stats import (get_rule_occurrences,
                                             word_rules_to_rules_dict)
from ordered_set import OrderedSet
from pandas import DataFrame


def get_fingerprint(speaker_word_rules: OrderedDictType[WordEntry, WordRules], speaker_phone_occurrences: PhoneOccurrences, speaker_phoneme_occurrences: PhonemeOccurrences, all_rules: OrderedSet[Rule]) -> Any:
  speaker_words_to_rules = word_rules_to_rules_dict(speaker_word_rules)
  speaker_rule_occurrences = get_rule_occurrences(speaker_words_to_rules, speaker_phone_occurrences)


def compare_two_fingerprints(fingerprint1: Any, fingerprint2: Any) -> float:
  pass


def cluster_fingerprints(fingerprints: List[Any]) -> float:
  pass
