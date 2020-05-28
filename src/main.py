import argparse

from src.rule_parser import get_rules_from_str, print_rules
from src.RuleHandler import apply_rules

def run(args):
  rules = get_rules_from_str(args.rules)
  print("Applying the following rules:")
  print_rules(rules)
  result = apply_rules(args.text, rules)

  print("Input: ", args.text)
  print("Output:", result)

if __name__ == "__main__":
  x = "Printing, differs from the arts and crafts represented in the Exhibition."
  x += " fist, forest, wolf, and village There this the test."
  parser = argparse.ArgumentParser()
  parser.add_argument('-t','--text', default=x, help='input text which should be transformed')
  parser.add_argument('-r','--rules', nargs='+', default='1<1> 2<0.5> 3<.1> 4 5<0> 6 7 8', help='rule<likelihood>..., order plays a role')
  args = parser.parse_args()
  run(args)
