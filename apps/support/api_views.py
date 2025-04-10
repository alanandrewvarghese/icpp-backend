from rest_framework import viewsets, permissions, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q
from .models import SupportTicket, TicketResponse
from .serializers import (
    SupportTicketSerializer,
    SupportTicketListSerializer,
    SupportTicketCreateSerializer,
    TicketResponseSerializer,
    TicketResponseCreateSerializer
)


class IsOwnerOrStaff(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object or staff members to access it.
    """
    def has_object_permission(self, request, view, obj):
        # Allow staff to access any object
        if request.user.is_staff:
            return True

        # Check if the object has a user attribute and if it matches the request user
        if hasattr(obj, 'user'):
            return obj.user == request.user

        # For responses, check if the related ticket belongs to the user
        if hasattr(obj, 'ticket'):
            return obj.ticket.user == request.user

        return False


class SupportTicketViewSet(viewsets.ModelViewSet):
    """
    API endpoint for support tickets.
    Students can create tickets and view/update their own tickets.
    Staff can view and manage all tickets.
    """
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'description']
    ordering_fields = ['created_at', 'updated_at', 'status']
    ordering = ['-created_at']

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return SupportTicket.objects.all()
        return SupportTicket.objects.filter(user=user)

    def get_serializer_class(self):
        if self.action == 'create':
            return SupportTicketCreateSerializer
        elif self.action == 'list':
            return SupportTicketListSerializer
        return SupportTicketSerializer

    def get_permissions(self):
        """
        Instantiates and returns the list of permissions that this view requires.
        """
        if self.action in ['retrieve', 'update', 'partial_update', 'destroy']:
            permission_classes = [permissions.IsAuthenticated, IsOwnerOrStaff]
        else:
            permission_classes = [permissions.IsAuthenticated]
        return [permission() for permission in permission_classes]

    def perform_create(self, serializer):
        """Set the user automatically based on the request."""
        serializer.save(user=self.request.user)

    @action(detail=True, methods=['post'])
    def add_response(self, request, pk=None):
        """
        Add a response to a ticket.
        """
        ticket = self.get_object()
        serializer = TicketResponseCreateSerializer(data=request.data)

        if serializer.is_valid():
            TicketResponse.objects.create(
                ticket=ticket,
                user=request.user,
                message=serializer.validated_data['message'],
                is_admin_response=request.user.is_staff
            )
            # Return the updated ticket with the new response
            return Response(
                SupportTicketSerializer(ticket).data,
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def my_tickets(self, request):
        """
        Return only the user's tickets.
        """
        queryset = SupportTicket.objects.filter(user=request.user).order_by('-created_at')
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = SupportTicketListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = SupportTicketListSerializer(queryset, many=True)
        return Response(serializer.data)


class AdminTicketViewSet(viewsets.ModelViewSet):
    """
    API endpoint for staff to manage tickets.
    """
    queryset = SupportTicket.objects.all().order_by('-created_at')
    serializer_class = SupportTicketSerializer
    permission_classes = [permissions.IsAuthenticated, permissions.IsAdminUser]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'description', 'user__username', 'user__email']
    ordering_fields = ['created_at', 'updated_at', 'status', 'user__username']
    ordering = ['-created_at']

    def get_serializer_class(self):
      if self.action == 'list' or self.action in ['open_tickets', 'search']:
          return SupportTicketListSerializer
      return SupportTicketSerializer

    @action(detail=True, methods=['post'])
    def change_status(self, request, pk=None):
        """
        Change the status of a ticket.
        """
        ticket = self.get_object()
        new_status = request.data.get('status')

        if new_status not in dict(SupportTicket.TicketStatus.choices):
            return Response(
                {'status': ['Invalid status. Choose from: ' + ', '.join(dict(SupportTicket.TicketStatus.choices).keys())]},
                status=status.HTTP_400_BAD_REQUEST
            )

        ticket.status = new_status
        ticket.save()

        # Optionally add an admin response noting the status change
        if request.data.get('add_note', False):
            note = request.data.get('note', f"Status changed to {ticket.get_status_display()}")
            TicketResponse.objects.create(
                ticket=ticket,
                user=request.user,
                message=note,
                is_admin_response=True
            )

        return Response(SupportTicketSerializer(ticket).data)

    @action(detail=False, methods=['get'])
    def open_tickets(self, request):
        """
        Return only open tickets.
        """
        queryset = SupportTicket.objects.filter(status=SupportTicket.TicketStatus.OPEN).order_by('-created_at')
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def search(self, request):
        """
        Advanced search endpoint for admins.
        """
        query = request.query_params.get('q', '')
        ticket_type = request.query_params.get('type', '')
        status = request.query_params.get('status', '')

        queryset = SupportTicket.objects.all()

        # Apply filters
        if query:
            queryset = queryset.filter(
                Q(title__icontains=query) |
                Q(description__icontains=query) |
                Q(user__username__icontains=query) |
                Q(user__email__icontains=query)
            )

        if ticket_type:
            queryset = queryset.filter(ticket_type=ticket_type)

        if status:
            queryset = queryset.filter(status=status)

        queryset = queryset.order_by('-created_at')

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
