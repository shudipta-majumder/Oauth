from logging import getLogger

import requests
from decouple import config

logging = getLogger("auth_users.services.hrms_service")


class HRMSService:
    """
    A HRMS Information Parser API
    """

    server_url = config("EXT_HRMS_API_LINK")

    def __init__(self) -> None:
        pass

    def get_employee_detail(self, employee_id: int):
        response = requests.get(f"{self.server_url}/public/emp/details/{employee_id}")
        try:
            # API is not returning any 404 or any other validation error.
            # For all kind of response API returning 200 response. So to
            # differentiate the response type success and failure intentionally
            # using `response.json()` directly as is body has no data then
            # this response will failed and will raise a python JSONDecodeError
            # for this using Try/Except to handle this situation gracefully.
            return 200, response.json()
        except requests.exceptions.JSONDecodeError:
            logging.error(f"hrms employee not found with id={employee_id!r}")
            return 404, {"code": 404, "message": "Employee not found !"}
        except Exception as error:
            logging.exception(error.args, stack_info=True)
            return 500, {"code": 500, "message": " | ".join(error.args)}
