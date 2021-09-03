from damm import Damm
from hypothesis import given
from hypothesis.strategies import integers


@given(integers(0, 1 << 512))
def test_num_checks_verify(num):
    """Assert the generated Damm check for number verifies."""

    assert Damm.verify(Damm.encode(num))
