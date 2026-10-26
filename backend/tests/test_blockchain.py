from app.services.blockchain import _eip1559_fees


def test_eip1559_max_fee_always_covers_priority_fee():
    priority_fee, max_fee = _eip1559_fees(base_fee=10, suggested_priority_fee=100)

    assert priority_fee == 100
    assert max_fee >= priority_fee


def test_eip1559_uses_two_base_fees_plus_priority():
    priority_fee, max_fee = _eip1559_fees(base_fee=25, suggested_priority_fee=3)

    assert priority_fee == 3
    assert max_fee == 53
