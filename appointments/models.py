from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    ROLE_CHOICES = (
        ("admin", "Admin"),
        ("doctor", "Doctor"),
        ("patient", "Patient"),
    )
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default="patient")
    middle_name = models.CharField(max_length=150, blank=True)

    def is_admin(self):
        return self.role == "admin"

    def is_doctor(self):
        return self.role == "doctor"

    def is_patient(self):
        return self.role == "patient"


class Clinic(models.Model):
    name = models.CharField(max_length=255)
    legal_address = models.TextField(blank=True)
    physical_address = models.TextField(blank=True)

    def __str__(self):
        return self.name


class Doctor(models.Model):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="doctor_profile"
    )
    specialization = models.CharField(max_length=255, blank=True)
    clinics = models.ManyToManyField(Clinic, related_name="doctors", blank=True)

    @property
    def first_name(self):
        return self.user.first_name

    @property
    def last_name(self):
        return self.user.last_name

    @property
    def middle_name(self):
        return self.user.middle_name

    @property
    def full_name(self):
        parts = [self.last_name, self.first_name, self.middle_name]
        return " ".join(p for p in parts if p)

    def __str__(self):
        return f"{self.full_name} ({self.specialization})"


class Patient(models.Model):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="patient_profile"
    )
    phone = models.CharField(max_length=30, blank=True)
    email = models.EmailField(blank=True)

    @property
    def first_name(self):
        return self.user.first_name

    @property
    def last_name(self):
        return self.user.last_name

    @property
    def middle_name(self):
        return self.user.middle_name

    @property
    def full_name(self):
        parts = [self.last_name, self.first_name, self.middle_name]
        return " ".join(p for p in parts if p)

    def __str__(self):
        return self.full_name


class Consultation(models.Model):
    STATUS_PENDING = "pending"
    STATUS_CONFIRMED = "confirmed"
    STATUS_STARTED = "started"
    STATUS_COMPLETED = "completed"
    STATUS_PAID = "paid"

    STATUS_CHOICES = (
        (STATUS_CONFIRMED, "Подтверждена"),
        (STATUS_PENDING, "Ожидает"),
        (STATUS_STARTED, "Начата"),
        (STATUS_COMPLETED, "Завершена"),
        (STATUS_PAID, "Оплачена"),
    )

    created_at = models.DateTimeField(auto_now_add=True)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING
    )

    doctor = models.ForeignKey(
        Doctor, on_delete=models.PROTECT, related_name="consultations"
    )
    patient = models.ForeignKey(
        Patient, on_delete=models.PROTECT, related_name="consultations"
    )
    clinic = models.ForeignKey(
        Clinic,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="consultations",
    )

    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Consultation #{self.pk} ({self.doctor} - {self.patient})"
