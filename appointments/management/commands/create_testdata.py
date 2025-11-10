from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from appointments.models import Clinic, Doctor, Patient, Consultation
from django.utils import timezone
from datetime import timedelta

User = get_user_model()


class Command(BaseCommand):
    help = "Create test users: admin, doctor, patient, clinic and a sample consultation"

    def handle(self, *args, **options):
        # ---------------- Admin ----------------
        admin, _ = User.objects.get_or_create(
            username="admin",
            defaults={
                "email": "admin@example.com",
                "role": "admin",
                "is_superuser": True,
                "is_staff": True,
            },
        )
        admin.set_password("123456")
        admin.save()

        # ---------------- Clinic ----------------
        clinic, _ = Clinic.objects.get_or_create(
            name="Medsi",
            defaults={
                "legal_address": "Legal Addr 1",
                "physical_address": "Physical Addr 1",
            },
        )

        # ---------------- Doctor ----------------
        doc_user, _ = User.objects.get_or_create(
            username="doctor_alex",
            defaults={
                "first_name": "Алексей",
                "last_name": "Борисов",
                "middle_name": "Игоревич",
                "email": "dr.alex@example.com",
                "role": "doctor",
            },
        )
        doc_user.set_password("doctor")
        doc_user.save()

        doctor, _ = Doctor.objects.get_or_create(
            user=doc_user,
            defaults={"specialization": "Терапевт"},
        )
        doctor.clinics.add(clinic)

        # ---------------- Patient ----------------
        pat_user, _ = User.objects.get_or_create(
            username="patient_anna",
            defaults={
                "first_name": "Анна",
                "last_name": "Иванова",
                "middle_name": "Сергеевна",
                "email": "anna@example.com",
                "role": "patient",
            },
        )
        pat_user.set_password("patient")
        pat_user.save()

        patient, _ = Patient.objects.get_or_create(
            user=pat_user,
            defaults={
                "phone": "+1234567890",
                "email": "anna@example.com",
            },
        )

        # ---------------- Consultation ----------------
        now = timezone.now()
        start = now + timedelta(days=1)
        end = start + timedelta(minutes=30)

        Consultation.objects.get_or_create(
            doctor=doctor,
            patient=patient,
            start_time=start,
            end_time=end,
            defaults={
                "clinic": clinic,
                "status": Consultation.STATUS_PENDING,
            },
        )

        self.stdout.write(self.style.SUCCESS("✅ Test data created successfully"))
        self.stdout.write(
            """
Admin:    username=admin         password=123456
Doctor:   username=doctor_alex   password=doctor
Patient:  username=patient_anna  password=patient
"""
        )
