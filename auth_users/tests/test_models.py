import pytest
from django.contrib.auth import get_user_model

djangodb = pytest.mark.django_db


@djangodb
def test_create_superuser(superuser_factory):
    superuser = superuser_factory

    assert superuser.is_superuser is True
    assert superuser.is_management is True
    assert superuser.is_staff is True


@djangodb
def test_create_basic_user(basicuser_factory):
    basicuser = basicuser_factory

    assert basicuser.is_superuser is False
    assert basicuser.is_management is False
    assert basicuser.is_staff is False


@djangodb
def test_create_management_user(mgmtuser_factory):
    basicuser = mgmtuser_factory

    assert basicuser.is_superuser is False
    assert basicuser.is_management is True
    assert basicuser.is_staff is False


@djangodb
@pytest.mark.parametrize(
    ["username", "password"], [(None, "password"), ("nuser", None)]
)
def test_create_user_should_failed_on_username_null(username, password):
    with pytest.raises(ValueError):
        get_user_model().objects.create_user(username=username, password=password)


@djangodb
@pytest.mark.parametrize("basicuser_factory__username", ["Jhon Doe"])
def test_user_str_return_username(basicuser_factory):
    assert str(basicuser_factory) == "Jhon Doe"
