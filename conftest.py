import pytest
from pytest_factoryboy import register
from rest_framework import status
from rest_framework.test import APIClient

from tests import UserFactory

register(
    UserFactory,
    "superuser_factory",
    is_superuser=True,
    is_management=True,
    is_staff=True,
)
register(
    UserFactory,
    "mgmtuser_factory",
    is_superuser=False,
    is_management=True,
    is_staff=False,
)
register(
    UserFactory,
    "basicuser_factory",
    is_superuser=False,
    is_management=False,
    is_staff=False,
)
register(
    UserFactory,
    "demouser_factory",
    is_superuser=False,
    is_management=False,
    is_staff=False,
)


@pytest.fixture
def api_client() -> APIClient:
    yield APIClient()


@pytest.fixture
def password() -> str:
    return "Password@123"


@pytest.fixture
def basicuser_factory__username():
    """Override username as a separate fixture."""
    return "Jack"


@pytest.fixture
def authenticated_superuser(api_client, superuser_factory, password):
    body = {"username": superuser_factory.username, "password": password}
    login_response = api_client.post("/oauth2/token/", body, format="json")

    access_token = login_response.json().get("access_token")

    return (superuser_factory, access_token)


@pytest.fixture
def authenticated_basicuser(api_client, basicuser_factory, password):
    body = {"username": basicuser_factory.username, "password": password}
    login_response = api_client.post("/oauth2/token/", body, format="json")

    access_token = login_response.json().get("access_token")

    return (basicuser_factory, access_token)


@pytest.fixture
def superuser_session(api_client, superuser_factory, password) -> APIClient:
    body = {"username": superuser_factory.username, "password": password}
    login_response = api_client.post("/oauth2/token/", body, format="json")
    assert login_response.status_code == status.HTTP_200_OK
    access_token = login_response.json().get("access_token")
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")
    yield client, superuser_factory


@pytest.fixture
def basicuser_session(api_client, basicuser_factory, password) -> APIClient:
    body = {"username": basicuser_factory.username, "password": password}
    login_response = api_client.post("/oauth2/token/", body, format="json")
    assert login_response.status_code == status.HTTP_200_OK
    access_token = login_response.json().get("access_token")
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")
    yield client, basicuser_factory
