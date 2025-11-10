from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Clinic, Doctor, Patient, Consultation
from django.db import IntegrityError, transaction

User = get_user_model()


class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    role = serializers.ChoiceField(choices=User.ROLE_CHOICES)

    class Meta:
        model = User
        fields = (
            "username",
            "first_name",
            "middle_name",
            "last_name",
            "password",
            "email",
            "role",
        )

    def create(self, validated_data):
        try:
            with transaction.atomic():
                password = validated_data.pop("password")
                role = validated_data.pop("role")

                user = User(**validated_data)
                user.role = role

                if role == "admin":
                    user.is_staff = True
                    user.is_superuser = True

                user.set_password(password)
                user.save()

                if role == "doctor":
                    Doctor.objects.create(user=user)
                elif role == "patient":
                    Patient.objects.create(user=user)

                return user

        except IntegrityError as e:
            raise serializers.ValidationError(
                {"detail": "Database integrity error", "error": str(e)}
            )


class ClinicSerializer(serializers.ModelSerializer):
    class Meta:
        model = Clinic
        fields = "__all__"


class DoctorSerializer(serializers.ModelSerializer):
    user = UserCreateSerializer()

    first_name = serializers.CharField(source="user.first_name", read_only=True)
    last_name = serializers.CharField(source="user.last_name", read_only=True)
    middle_name = serializers.CharField(source="user.middle_name", read_only=True)

    class Meta:
        model = Doctor
        fields = (
            "id",
            "user",
            "first_name",
            "last_name",
            "middle_name",
            "specialization",
            "clinics",
        )


class PatientSerializer(serializers.ModelSerializer):
    user = UserCreateSerializer()

    first_name = serializers.CharField(source="user.first_name", read_only=True)
    last_name = serializers.CharField(source="user.last_name", read_only=True)
    middle_name = serializers.CharField(source="user.middle_name", read_only=True)

    class Meta:
        model = Patient
        fields = (
            "id",
            "user",
            "first_name",
            "last_name",
            "middle_name",
            "phone",
            "email",
        )


class ConsultationSerializer(serializers.ModelSerializer):
    doctor_id = serializers.PrimaryKeyRelatedField(
        queryset=Doctor.objects.all(), source="doctor", write_only=True
    )
    patient_id = serializers.PrimaryKeyRelatedField(
        queryset=Patient.objects.all(), source="patient", write_only=True
    )
    doctor = DoctorSerializer(read_only=True)
    patient = PatientSerializer(read_only=True)

    class Meta:
        model = Consultation
        fields = (
            "id",
            "created_at",
            "start_time",
            "end_time",
            "status",
            "doctor_id",
            "patient_id",
            "doctor",
            "patient",
            "clinic",
            "notes",
        )
        read_only_fields = ("created_at",)

    def validate(self, data):
        # validate that start < end
        start = data.get("start_time")
        end = data.get("end_time")
        if start and end and start >= end:
            raise serializers.ValidationError("end_time must be after start_time")
        return data

    def create(self, validated_data):
        try:
            return super().create(validated_data)
        except IntegrityError as e:
            raise serializers.ValidationError(
                {"detail": "Database integrity error", "error": str(e)}
            )
