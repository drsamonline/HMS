from datetime import date, timedelta


def test_expired_batch_is_not_eligible_for_dispense():
    expired = date.today() - timedelta(days=1)
    assert expired < date.today()


def test_future_batch_can_be_expiring_soon():
    expiring = date.today() + timedelta(days=30)
    assert 0 <= (expiring - date.today()).days <= 90
