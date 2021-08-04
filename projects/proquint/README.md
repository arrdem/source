# Proquint

An implementation of [A Proposal for Proquints](https://arxiv.org/html/0901.4016).

To summarize the paper, traditional decimal and hexadecimal codings are inconvenient for "large" bit-width identifiers.
Decimal and hexadecimal codings offer no obvious dense enunciation and are traditionally presented without segmentation punctuation.
The proquint format is a semantically dense coding for 16 bit hunks fitting within the enunciable space of English.

## Demo

``` python
>>> from proquint import Proquint
>>> Proquint.encode_i16(0)
'babab'
>>> Proquint.encode_i16(1)
'babad'
>>> Proquint.encode_i64(14708250061244963317)
'subiv-gavab-sobiz-noluj'
>>> Proquint.decode('babad')
1
```

## API Overview

### `proquint.Proquint.CONSONANTS`

A string of consonants to use when encoding or decoding proquints.
Must be of length 16.

### `proquint.Proquint.VOWELS`

A string of vowels to use when encoding or decoding proquints.
Must be of length 4.

### `proquint.Proquint.decode(buffer: str) -> int`

Decode a proquint string to an integer value without restriction on bit-width.

### `proquint.Proquint.encode(val: int, width: int) -> str`

Encode an integer into a string which will decode to the same value.

Note that the bit-width must be specified in order to determine the number of required segments.

### `proquint.Proquint.encode_{i16, i32, i64}(val: int) -> str`

Helpers for encoding known-width quantities.

## LICENSE

Copyright Reid 'arrdem' McKenzie August 2021.

Published under the terms of the MIT license.
