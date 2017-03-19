from anom import delete_multi, get_multi, put_multi


def test_delete_multi_can_be_called_with_empty_list():
    assert delete_multi([]) is None


def test_get_and_multi_can_be_called_with_empty_list():
    for fn in (get_multi, put_multi):
        assert fn([]) == []
