from rest_framework import viewsets, mixins, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.db import DatabaseError

from .models import Consultation
from .serializers import (
    ConsultationSerializer,
    UserCreateSerializer,
)
from .permissions import ConsultationPermission


class RegistrationViewSet(mixins.CreateModelMixin, viewsets.GenericViewSet):
    serializer_class = UserCreateSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(
                {"detail": "User created successfully"}, status=status.HTTP_201_CREATED
            )
        except DatabaseError as e:
            return Response(
                {"detail": f"Database error: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class ConsultationViewSet(viewsets.ModelViewSet):
    queryset = Consultation.objects.select_related(
        "doctor__user", "patient__user", "clinic"
    ).all()
    serializer_class = ConsultationSerializer
    permission_classes = [IsAuthenticated, ConsultationPermission]
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]

    filterset_fields = ["status", "clinic__id", "doctor__id", "patient__id"]

    search_fields = [
        "doctor__user__first_name",
        "doctor__user__last_name",
        "doctor__user__middle_name",
        "patient__user__first_name",
        "patient__user__last_name",
        "patient__user__middle_name",
    ]

    ordering_fields = ["created_at", "start_time"]
    ordering = ["-created_at"]

    def get_queryset(self):
        user = self.request.user
        qs = super().get_queryset()

        if user.is_admin():
            return qs
        if user.is_doctor():
            return qs.filter(doctor__user=user)
        if user.is_patient():
            return qs.filter(patient__user=user)
        return Consultation.objects.none()

    def perform_create(self, serializer):
        user = self.request.user
        if user.is_admin() or user.is_patient():
            serializer.save()
        else:
            from rest_framework.exceptions import PermissionDenied

            raise PermissionDenied("Only patients or admins can create consultations.")

    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated])
    def change_status(self, request, pk=None):
        consultation = self.get_object()
        new_status = request.data.get("status")

        if not new_status:
            return Response(
                {"detail": "Status is required"}, status=status.HTTP_400_BAD_REQUEST
            )

        if new_status not in dict(Consultation.STATUS_CHOICES).keys():
            return Response(
                {"detail": "Invalid status value"}, status=status.HTTP_400_BAD_REQUEST
            )

        user = request.user

        if not (
            user.is_admin()
            or (user.is_doctor() and consultation.doctor.user_id == user.id)
            or (user.is_patient() and consultation.patient.user_id == user.id)
        ):
            return Response(
                {"detail": "Permission denied"}, status=status.HTTP_403_FORBIDDEN
            )

        consultation.status = new_status
        consultation.save()
        return Response(
            self.get_serializer(consultation).data, status=status.HTTP_200_OK
        )
