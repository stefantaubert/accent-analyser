from collections import OrderedDict
from typing import Any, List, Optional
from typing import OrderedDict as OrderedDictType
from typing import Set, Tuple

import numpy as np
from accent_analyser.core.rule_detection import (PhonemeOccurrences,
                                                 PhoneOccurrences, Rule,
                                                 RuleType, WordEntry,
                                                 WordRules, rule_to_str,
                                                 rules_to_str)
from accent_analyser.core.rule_stats import (get_rule_occurrences,
                                             word_rules_to_rules_dict)
from ordered_set import OrderedSet
from pandas import DataFrame
from scipy.cluster.hierarchy import dendrogram
from sklearn.cluster import AgglomerativeClustering


def get_fingerprint(speaker_word_rules: OrderedDictType[WordEntry, WordRules], speaker_phone_occurrences: PhoneOccurrences, speaker_phoneme_occurrences: PhonemeOccurrences, all_rules: OrderedSet[Rule]) -> Any:
  speaker_words_to_rules = word_rules_to_rules_dict(speaker_word_rules)
  speaker_rule_occurrences = get_rule_occurrences(speaker_words_to_rules, speaker_phone_occurrences)
  speaker_rule_relative_occurence = speaker_rule_occurrences.copy()
  for rule in list(speaker_words_to_rules.keys()):
    norm_factor = 0
    for word in speaker_words_to_rules[rule]:
      grapheme_and_phoneme = (word.graphemes, word.phonemes)
      norm_factor += speaker_phoneme_occurrences[(grapheme_and_phoneme)]
    speaker_rule_relative_occurence[rule] /= norm_factor
  fingerprint = get_vector(speaker_rule_relative_occurence, all_rules)
  return fingerprint


def get_vector(rule_occurences, all_rules):
  vector = [rule_occurences[rule] if rule in rule_occurences.keys() else 0 for rule in all_rules]
  return np.array(vector)


def compare_two_fingerprints(fingerprint1: Any, fingerprint2: Any) -> float:
  pass


def cluster_fingerprints(fingerprints: List[Any]) -> float:
  AggloClust = AgglomerativeClustering(distance_threshold=0, n_clusters=None)
  clustering = AggloClust.fit(fingerprints)
  plot_dendrogram(clustering)


def plot_dendrogram(model, **kwargs):
    # Create linkage matrix and then plot the dendrogram

    # create the counts of samples under each node
  counts = np.zeros(model.children_.shape[0])
  n_samples = len(model.labels_)
  for i, merge in enumerate(model.children_):
    current_count = 0
    for child_idx in merge:
      if child_idx < n_samples:
        current_count += 1  # leaf node
      else:
        current_count += counts[child_idx - n_samples]
    counts[i] = current_count

  linkage_matrix = np.column_stack([model.children_, model.distances_,
                                    counts]).astype(float)

  # Plot the corresponding dendrogram
  dendrogram(linkage_matrix, **kwargs)
