# Damm

An implementation of a Damm check digits.

doi:10.2174/9781608058822114010013

To get into the group theory here a bit, Damm showed that it was possible to construct an anti-symmetric quasigroup for most orders (group sizes).
A quasigroup is a non-associative group for which division is always well defined.
Damm's check digits are based on this non-associative property which allows for the full detection of transposition errors.

We can use a quasigroup to implement a check digit scheme.
Checking a number consists of "multiplying" the digits of the number together through the group's multiplication table.

The neat bit of Damm's quasigroups is the property `x · x = 0`.
This is visible in the multiplication matrix below.
What this means is that if the Damm code (product of all digits within the Damm group!)
of a numeric string is x, the product of THAT product with itself is 0.
Which means we can compute the Damm coding of any number simply by APPENDING the product of its digits.

Damm checking is then defined by computing the product of the digits within a Damm group and affirming that the product is 0 which is only possible if the input string is '0' OR it is a valid Damm checked number.

Another nice trick with the Damm quasigroup is that it's safe to PREFIX zeros to any Damm coded number without changing the Damm correction code.
Unfortunately this also means that SUFFIXING zeros won't impact the Damm code either.
