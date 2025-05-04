# 📑 One Stop Solution (OSS)

This is a RestAPI for the *One Stop Solution (OSS)*, built using Django and Django Rest Framework (DRF).

## Features

- Digital Party Management System (Ongoing)
- Corporate Price Quotation (Pending Integration)
- Guest Management System (Pending Integration)

## Getting Started

To get started with this project, follow these steps:

1. Clone the repository:

```bash
git clone https://github.com/digitech-IT/party-management-system-backend.git
cd party-management-system-backend
```

2. Create a virtual environment and install the required dependencies:

```bash
poetry shell
poetry install
```

3. Apply the database migrations:

```bash
python manage.py makemigrations
python manage.py migrate
```

4. Create a superuser account for administrative access:

```bash
python manage.py createsuperuser
```

5. Start the development server:

```bash
python manage.py runserver
```

or if you are used to makefile then use:

```bash
make run
```

## Celery Worker

install the redis using below command

```bash
sudo apt-get install redis
sudo systemctl enable redis
sudo systemctl status redis
```

then run the celery worker with below command

```bash
celery -A core worker --loglevel=INFO
```
or for windows
```bash
celery -A core worker --loglevel=INFO --logfile=./logs/celery.log --pool=solo
```

## Testing

To run the tests just type below command

```bash
make test
```

## Documentation

To check the `Swagger-UI` documentation of the API or to execute the API documentation in a local environment after spinning up the local development server open the below URL.

```bash
http://127.0.0.1:8000/api/docs
```

or if you prefer `Redoc` then

```bash
http://127.0.0.1:8000/api/redoc
```

## Contact

If you have any questions or need assistance, feel free to contact us at [computer.it21@waltonbd.com](mailto:computer.it21@waltonbd.com).

Happy coding!
