from anom import delete_multi, get_multi, put_multi, lookup_model_by_kind

from .models import Person


def test_can_look_up_known_models_by_kind():
    assert lookup_model_by_kind("Person") is Person


def test_can_fail_to_look_up_unknown_models_by_kind():
    assert lookup_model_by_kind("UnknownKind") is None


def test_delete_multi_can_be_called_with_empty_list():
    assert delete_multi([]) is None


def test_get_and_multi_can_be_called_with_empty_list():
    for fn in (get_multi, put_multi):
        assert fn([]) == []
