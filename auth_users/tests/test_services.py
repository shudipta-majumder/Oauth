import pytest
from rest_framework import status

from auth_users.services.hrms_service import HRMSService

djangodb = pytest.mark.django_db


@pytest.fixture
def hrms_service() -> HRMSService:
    return HRMSService()


def test_hrms_service_object_init_working(hrms_service: HRMSService) -> None:
    assert isinstance(hrms_service, HRMSService)


def test_hrms_service_return_404_when_not_found(hrms_service: HRMSService) -> None:
    req_status, response = hrms_service.get_employee_detail(-54681)
    assert req_status == status.HTTP_404_NOT_FOUND
    assert response is None


def test_hrms_service_returns_data_when_found(hrms_service: HRMSService) -> None:
    expected = {
        "email": "it.dba-inc@waltonbd.com",
        "displayName": "Sanjay Kumar Roy",
        "phone": "01678049643",
        "designation": "First Senior Deputy Executive Director",
    }
    req_status, response = hrms_service.get_employee_detail(43097)
    assert req_status == status.HTTP_200_OK
    assert response == expected
