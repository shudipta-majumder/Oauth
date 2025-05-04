from rest_framework.test import APITestCase

from tests.user_factories import UserFactory


class TestBaseSetup(APITestCase):
    def setUp(self) -> None:
        self.base_url = "/api/v1/auth"
        self.login_url = ""
        self.logout_url = None
        self.common_pwd = "Password@123"
        # normal test user
        self.fake_user = UserFactory()
        self.fake_user.save()
        # dummy users
        self.dummy_user_1 = UserFactory()
        self.dummy_user_1.save()
        self.dummy_user_2 = UserFactory()
        self.dummy_user_2.save()
        # admin user
        self.fake_admin_user = UserFactory()
        self.fake_admin_user.is_superuser = True
        self.fake_admin_user.is_management = True
        self.fake_admin_user.is_staff = True
        self.fake_admin_user.save()

        return super().setUp()

    def tearDown(self) -> None:
        return super().tearDown()
