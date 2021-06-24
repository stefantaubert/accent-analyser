import epitran

epi = epitran.Epitran('eng-Latn')

_punct_str = '!"#$%&\'()*+,-./:;<=>/?@[\\]^_`{|}~«» '

class InputWord():

  def __init__(self, token: str):
    super().__init__()
    self._token = token.lower()
    self._replace_by = self._token.strip(_punct_str)
    self.content = self._replace_by

  def convert_to_ipa(self):
    if not self.is_empty():
      self.content = epi.transliterate(self.content)

  def update(self, word):
    self.content = word

  def is_empty(self):
    return self.content == ""

  def get_result(self):
    return self._token.replace(self._replace_by, self.content)
