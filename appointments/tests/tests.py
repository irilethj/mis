import os
import sys

import pytest
import django

from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model

from appointments.models import Doctor, Patient, Clinic, Consultation

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mis.settings")
django.setup()

User = get_user_model()


def get_jwt_token(client, username, password):
    url = reverse("token_obtain_pair")
    response = client.post(
        url, {"username": username, "password": password}, format="json"
    )
    assert response.status_code == status.HTTP_200_OK
    return response.data["access"]


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def create_users(db):
    # Админ
    admin = User.objects.create_user(
        username="admin",
        password="adminpass",
        role="admin",
        is_staff=True,
        is_superuser=True,
    )

    # Доктор
    doctor_user = User.objects.create_user(
        username="doc", password="docpass", role="doctor"
    )
    doctor = Doctor.objects.create(user=doctor_user)

    # Пациент
    patient_user = User.objects.create_user(
        username="pat", password="patpass", role="patient"
    )
    patient = Patient.objects.create(user=patient_user)

    return {"admin": admin, "doctor": doctor, "patient": patient}


@pytest.fixture
def create_clinic(db):
    return Clinic.objects.create(name="Test Clinic")


@pytest.mark.django_db
def test_user_registration(api_client):
    url = reverse("register-list")
    data = {
        "username": "newpatient",
        "password": "strongpassword",
        "role": "patient",
        "first_name": "John",
        "last_name": "Doe",
        "middle_name": "A",
        "email": "john@example.com",
    }
    response = api_client.post(url, data, format="json")
    assert response.status_code == status.HTTP_201_CREATED
    assert User.objects.filter(username="newpatient").exists()


@pytest.mark.django_db
def test_patient_can_create_consultation(api_client, create_users, create_clinic):
    patient = create_users["patient"]
    doctor = create_users["doctor"]

    token = get_jwt_token(api_client, patient.user.username, "patpass")
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

    url = reverse("consultation-list")
    data = {
        "doctor_id": doctor.id,
        "patient_id": patient.id,
        "clinic": create_clinic.id,
        "start_time": "2030-01-01T10:00:00Z",
        "end_time": "2030-01-01T11:00:00Z",
        "notes": "Test consultation",
    }
    response = api_client.post(url, data, format="json")

    assert response.status_code == status.HTTP_201_CREATED
    assert Consultation.objects.count() == 1


@pytest.mark.django_db
def test_doctor_cannot_create_consultation(api_client, create_users, create_clinic):
    doctor = create_users["doctor"]
    patient = create_users["patient"]

    token = get_jwt_token(api_client, doctor.user.username, "docpass")
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

    url = reverse("consultation-list")
    data = {
        "doctor_id": doctor.id,
        "patient_id": patient.id,
        "clinic": create_clinic.id,
        "start_time": "2030-01-01T10:00:00Z",
        "end_time": "2030-01-01T11:00:00Z",
        "notes": "Doctor should not create",
    }
    response = api_client.post(url, data, format="json")
    assert response.status_code == status.HTTP_403_FORBIDDEN
