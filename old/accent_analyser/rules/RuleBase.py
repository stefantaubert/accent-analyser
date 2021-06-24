from random import random

class RuleBase():
  def __init__(self, likelihood=1.0):
    super().__init__()
    self.likelihood = likelihood
    self.name = "unnamed rule"

  def should_convert(self):
    # random() -> [0.0, 1.0)
    do_convert = self.likelihood == 1.0 or random() < self.likelihood
    return do_convert
