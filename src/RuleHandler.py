
from src.InputWordList import InputWordList

def parse_sentences(text: str):
  sentences = text.split('.')
  output_sentences = [sentence for sentence in sentences if len(sentence) > 0]
  return output_sentences

def apply_rules(text: str, rules: list):
  sentences = parse_sentences(text)
  output_sentences = []
  for sentence in sentences:
    wordlist = InputWordList(sentence)
    result = wordlist.transform(rules)
    output_sentences.append(result)
  output_text = '. '.join(output_sentences).rstrip()
  return output_text
  