how	hˈaʊ	hˈaʊ	Unchanged	20	38	52.63
how	hˈaʊ	xˈaʊ	S(h;x;1)	14	38	36.84
how	hˈaʊ	xˈa	S(h;x;1), O(ʊ;5)	3	38	7.89
how	hˈaʊ	hˈa	O(ʊ;4)	1	38	2.63

h ˈ a ʊ;;;;52.63
h ˈ a ʊ;(S;x;1);36.84
h ˈ a ʊ;(S;x;1);(O;5);7.89
h ˈ a ʊ;(O;4);1.63
h ˈ a ʊ;(I;5;x);1.00

from    to    probability
h ˈ a ʊ x ˈ a ʊ  52.63

```json
{
  {
    "phonemes": ["h", "ˈ", "a", "ʊ"],
    "probability": 52.63,
    "rules": [],
  },
  {
    "phonemes": ["h", "ˈ", "a", "ʊ"],
    "probability": 36.84,
    "rules": [
      {
        "type": "S",
        "positions": [1],
        "symbols": ["x"],
      }
    ],
  },
  {
    "phonemes": ["h", "ˈ", "a", "ʊ"],
    "probability": 7.89,
    "rules": [
      {
        "type": "S",
        "positions": [1],
        "symbols": ["x"],
      },
      {
        "type": "O",
        "positions": [4],
      },
      {
        "type": "I",
        "positions": [4],
        "symbols": ["x"],
      }
    ],
  }
}
```

```json
{
  {
    "phonemes": ["h", "ˈ", "a", "ʊ"],
    "rules": [
      {
        "entries": [],
        "probability": 52.63,
      },
      {
        "entries": [
          {
            "type": "S",
            "positions": [1],
            "symbols": ["x"],
          }
        ],
        "probability": 52.63,
      },
    ]
  },
}
```
