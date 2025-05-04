import factory

from auth_users.models import User


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User

    username = factory.Faker("user_name")
    password = factory.PostGenerationMethodCall("set_password", "Password@123")
    email = factory.Faker("email")
    full_name = factory.Faker("name")
    phone = factory.Faker("isbn13")
    is_superuser = True
    is_management = True
    is_staff = True
