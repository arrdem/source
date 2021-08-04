from damm import Damm
import pytest


@pytest.mark.parametrize("num", [
    "0",    # 0 itself is the start Damm state
    "37",   # [0, 3] => 7
    "92",   # [0, 9] => 2
    "1234", # Amusingly, this is a 0-product.
])
def test_num_verifies(num):
    """Assert that known-good Damm checks pass."""

    assert Damm.verify(num)
