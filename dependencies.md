# Remote Dependencies

- text-utils
  - pronunciation_dict_parser
  - g2p_en
  - sentence2pronunciation

## Pipfile

### Local

```Pipfile
text-utils = {editable = true, path = "./../text-utils"}

pronunciation_dict_parser = {editable = true, path = "./../pronunciation_dict_parser"}
g2p_en = {editable = true, path = "./../g2p"}
sentence2pronunciation = {editable = true, path = "./../sentence2pronunciation"}
```

### Remote

```Pipfile
text-utils = {editable = true, ref = "master", git = "https://github.com/stefantaubert/text-utils.git"}
```

## setup.cfg

```cfg
text_utils@git+https://github.com/stefantaubert/text-utils.git@master
```
