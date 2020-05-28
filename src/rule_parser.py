import re

from src.rules.RuleHeShe import RuleHeShe
from src.rules.RuleInsert import RuleInsert
from src.rules.RuleInsertA import RuleInsertA
from src.rules.RuleOmit import RuleOmit
from src.rules.RuleRemoveThe import RuleRemoveThe
from src.rules.RuleSubstitue import RuleSubstitue
from src.rules.RuleSubstitue2 import RuleSubstitue2
from src.rules.VoicedFricative1 import VoicedFricative1

_r_match = "(\d+)(?:\<((?:[0]*\.\d*)|(?:0)|(?:1))\>)?"

_rules_dict = {
  '1': RuleOmit,
  '2': RuleInsert,
  '3': RuleSubstitue,
  '4': RuleSubstitue2,
  '5': RuleHeShe,
  '6': RuleRemoveThe,
  '7': RuleInsertA,
  '8': VoicedFricative1,
}

def get_rule(rule_id: str):
  result = re.match(_r_match, rule_id)
  is_valid = result != None
  if is_valid:
    rule, likelihood = result.groups()
    likelihood = float(likelihood) if likelihood != None else None
    if rule in _rules_dict.keys():
      rule_type = _rules_dict[rule]
      if likelihood == None:
        instance = rule_type()
      else:
        instance = rule_type(likelihood)
      return instance
    else:
      print('Rule {} unknown.'.format(rule))
      return None
      
  print('Invalid rule'.format(rule_id))
  return None

def get_rules_from_str(inp_str: str):
  rules = []
  for rule in inp_str.split(' '):
    rule_instance = get_rule(rule)
    if rule_instance != None:
      rules.append(rule_instance)
  return rules

def print_rules(rules: list):
  for rule in rules:
    print(" \'{}\' with likelihood of {:.0f}%".format(rule.name, rule.likelihood * 100))