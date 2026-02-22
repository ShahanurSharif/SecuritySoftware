from datetime import timedelta

from django.contrib.auth.models import User
from django.db.models import Q
from django.utils import timezone
from django_filters import rest_framework as django_filters
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import (
    ShiftTemplate, RosterShift, Availability,
    PTORequest, DropRequest, Notification,
)
from .serializers import (
    ShiftTemplateSerializer, RosterShiftSerializer, AvailabilitySerializer,
    PTORequestSerializer, DropRequestSerializer, NotificationSerializer,
)


# ===================================================================
# Filters
# ===================================================================

class RosterShiftFilter(django_filters.FilterSet):
    date_from = django_filters.DateFilter(field_name='date', lookup_expr='gte')
    date_to = django_filters.DateFilter(field_name='date', lookup_expr='lte')

    class Meta:
        model = RosterShift
        fields = ['user', 'branch', 'status', 'date_from', 'date_to']


class PTORequestFilter(django_filters.FilterSet):
    date_from = django_filters.DateFilter(field_name='start_date', lookup_expr='gte')
    date_to = django_filters.DateFilter(field_name='end_date', lookup_expr='lte')

    class Meta:
        model = PTORequest
        fields = ['user', 'leave_type', 'status', 'date_from', 'date_to']


# ===================================================================
# Helper — create in-app notification
# ===================================================================

def _notify(user, notification_type, title, message, shift=None):
    """Create an in-app notification for a user."""
    Notification.objects.create(
        user=user,
        notification_type=notification_type,
        channel='in_app',
        title=title,
        message=message,
        related_shift=shift,
    )


# ===================================================================
# Shift Template ViewSet
# ===================================================================

class ShiftTemplateViewSet(viewsets.ModelViewSet):
    queryset = ShiftTemplate.objects.select_related('branch').all()
    serializer_class = ShiftTemplateSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['branch', 'is_active']
    search_fields = ['name']
    ordering_fields = ['name', 'start_time', 'branch']


# ===================================================================
# Roster Shift ViewSet
# ===================================================================

class RosterShiftViewSet(viewsets.ModelViewSet):
    serializer_class = RosterShiftSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_class = RosterShiftFilter
    search_fields = ['user__first_name', 'user__last_name', 'branch__name']
    ordering_fields = ['date', 'start_time', 'user', 'branch', 'status']

    def get_queryset(self):
        qs = RosterShift.objects.select_related(
            'user', 'branch', 'template', 'created_by',
        ).prefetch_related('drop_requests')

        # LPO users only see their own shifts
        user = self.request.user
        if hasattr(user, 'profile') and user.profile.role == 'LPO':
            qs = qs.filter(user=user)
        return qs

    # --- Calendar endpoint: /api/roster/shifts/calendar/?month=2025-07 ---
    @action(detail=False, methods=['get'])
    def calendar(self, request):
        """Return shifts grouped by date for a given month."""
        month_str = request.query_params.get('month')  # YYYY-MM
        if not month_str:
            return Response({'error': 'month parameter required (YYYY-MM)'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            year, month = map(int, month_str.split('-'))
        except (ValueError, AttributeError):
            return Response({'error': 'Invalid month format. Use YYYY-MM.'}, status=status.HTTP_400_BAD_REQUEST)

        from calendar import monthrange
        _, last_day = monthrange(year, month)
        from datetime import date
        start = date(year, month, 1)
        end = date(year, month, last_day)

        qs = self.get_queryset().filter(date__gte=start, date__lte=end)
        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)

    # --- Conflict check: /api/roster/shifts/check_conflicts/ ---
    @action(detail=False, methods=['post'])
    def check_conflicts(self, request):
        """Check if a proposed shift conflicts with existing ones."""
        user_id = request.data.get('user')
        date_val = request.data.get('date')
        start_time = request.data.get('start_time')
        end_time = request.data.get('end_time')
        exclude_id = request.data.get('exclude_id')

        if not all([user_id, date_val, start_time, end_time]):
            return Response({'error': 'user, date, start_time, end_time required'}, status=status.HTTP_400_BAD_REQUEST)

        conflicts = RosterShift.objects.filter(
            user_id=user_id,
            date=date_val,
            status__in=('scheduled', 'confirmed'),
            start_time__lt=end_time,
            end_time__gt=start_time,
        )
        if exclude_id:
            conflicts = conflicts.exclude(pk=exclude_id)

        # Also check PTO
        pto_conflicts = PTORequest.objects.filter(
            user_id=user_id,
            status='approved',
            start_date__lte=date_val,
            end_date__gte=date_val,
        )

        # Check availability (date-based)
        availability_issue = False
        avail = Availability.objects.filter(user_id=user_id, date=date_val)
        if avail.exists():
            available_for_time = avail.filter(
                is_available=True,
                start_time__lte=start_time,
                end_time__gte=end_time,
            )
            if not available_for_time.exists():
                availability_issue = True

        return Response({
            'has_shift_conflict': conflicts.exists(),
            'shift_conflicts': RosterShiftSerializer(conflicts, many=True).data,
            'has_pto_conflict': pto_conflicts.exists(),
            'has_availability_issue': availability_issue,
        })

    # --- Bulk create shifts: /api/roster/shifts/bulk_create/ ---
    @action(detail=False, methods=['post'])
    def bulk_create(self, request):
        """Create multiple shifts at once (e.g. from a template or week copy)."""
        shifts_data = request.data.get('shifts', [])
        if not shifts_data:
            return Response({'error': 'shifts list required'}, status=status.HTTP_400_BAD_REQUEST)

        created = []
        errors = []
        for i, shift_data in enumerate(shifts_data):
            serializer = RosterShiftSerializer(data=shift_data, context={'request': request})
            if serializer.is_valid():
                shift = serializer.save()
                created.append(serializer.data)
                _notify(
                    shift.user, 'shift_assigned',
                    'New Shift Assigned',
                    f'You have been assigned a shift on {shift.date} '
                    f'at {shift.branch.name} ({shift.start_time:%H:%M}–{shift.end_time:%H:%M}).',
                    shift=shift,
                )
            else:
                errors.append({'index': i, 'errors': serializer.errors})

        return Response({'created': len(created), 'errors': errors},
                        status=status.HTTP_201_CREATED if created else status.HTTP_400_BAD_REQUEST)

    # --- Copy week: /api/roster/shifts/copy_week/ ---
    @action(detail=False, methods=['post'])
    def copy_week(self, request):
        """Copy all shifts from source_week_start to target_week_start."""
        from datetime import date as date_cls
        source = request.data.get('source_week_start')  # YYYY-MM-DD (Monday)
        target = request.data.get('target_week_start')

        if not source or not target:
            return Response({'error': 'source_week_start and target_week_start required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            source_date = date_cls.fromisoformat(source)
            target_date = date_cls.fromisoformat(target)
        except ValueError:
            return Response({'error': 'Invalid date format'}, status=status.HTTP_400_BAD_REQUEST)

        delta = target_date - source_date
        source_shifts = RosterShift.objects.filter(
            date__gte=source_date,
            date__lt=source_date + timedelta(days=7),
            status__in=('scheduled', 'confirmed'),
        )

        created = []
        for s in source_shifts:
            new_shift = RosterShift.objects.create(
                user=s.user,
                branch=s.branch,
                template=s.template,
                date=s.date + delta,
                start_time=s.start_time,
                end_time=s.end_time,
                status='scheduled',
                notes=f'Copied from {s.date}',
                created_by=request.user,
            )
            created.append(new_shift.pk)

        return Response({'created': len(created)}, status=status.HTTP_201_CREATED)

    def perform_create(self, serializer):
        shift = serializer.save()
        _notify(
            shift.user, 'shift_assigned',
            'New Shift Assigned',
            f'You have been assigned a shift on {shift.date} '
            f'at {shift.branch.name} ({shift.start_time:%H:%M}–{shift.end_time:%H:%M}).',
            shift=shift,
        )

    def perform_update(self, serializer):
        shift = serializer.save()
        _notify(
            shift.user, 'shift_updated',
            'Shift Updated',
            f'Your shift on {shift.date} at {shift.branch.name} has been updated.',
            shift=shift,
        )

    # --- Weekly hours summary: /api/roster/shifts/weekly_summary/?week_start=2026-02-16 ---
    @action(detail=False, methods=['get'])
    def weekly_summary(self, request):
        """Return per-user weekly hours & pay totals for a given week."""
        from datetime import date as date_cls
        week_start = request.query_params.get('week_start')
        if not week_start:
            return Response({'error': 'week_start parameter required (YYYY-MM-DD, Monday)'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            start = date_cls.fromisoformat(week_start)
        except ValueError:
            return Response({'error': 'Invalid date format'}, status=status.HTTP_400_BAD_REQUEST)

        end = start + timedelta(days=6)
        shifts = self.get_queryset().filter(
            date__gte=start, date__lte=end,
            status__in=('scheduled', 'confirmed', 'completed'),
        )

        user_summary = {}
        for s in shifts:
            uid = s.user_id
            if uid not in user_summary:
                user_summary[uid] = {
                    'user_id': uid,
                    'user_name': f'{s.user.first_name} {s.user.last_name}'.strip() or s.user.username,
                    'total_hours': 0,
                    'total_pay': 0,
                    'shift_count': 0,
                    'daily': {},
                }
            entry = user_summary[uid]
            entry['total_hours'] += s.total_hours
            entry['total_pay'] += s.total_pay
            entry['shift_count'] += 1
            day_str = str(s.date)
            if day_str not in entry['daily']:
                entry['daily'][day_str] = {'hours': 0, 'pay': 0, 'shifts': 0}
            entry['daily'][day_str]['hours'] += s.total_hours
            entry['daily'][day_str]['pay'] += s.total_pay
            entry['daily'][day_str]['shifts'] += 1

        # Round totals
        for u in user_summary.values():
            u['total_hours'] = round(u['total_hours'], 2)
            u['total_pay'] = round(u['total_pay'], 2)
            for d in u['daily'].values():
                d['hours'] = round(d['hours'], 2)
                d['pay'] = round(d['pay'], 2)

        return Response({
            'week_start': str(start),
            'week_end': str(end),
            'users': list(user_summary.values()),
        })


# ===================================================================
# Availability ViewSet
# ===================================================================

class AvailabilityViewSet(viewsets.ModelViewSet):
    serializer_class = AvailabilitySerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['user', 'date', 'is_available', 'preset']
    ordering_fields = ['date', 'start_time']

    def get_queryset(self):
        qs = Availability.objects.select_related('user')
        user = self.request.user
        if hasattr(user, 'profile') and user.profile.role == 'LPO':
            qs = qs.filter(user=user)
        return qs

    # --- LPO availability matrix for a week ---
    @action(detail=False, methods=['get'])
    def lpo_matrix(self, request):
        """Return LPO users availability matrix for a given week."""
        from datetime import date as date_cls, timedelta as td
        from profiles.models import Profile

        week_start_str = request.query_params.get('week_start')
        if not week_start_str:
            today = date_cls.today()
            week_start = today - td(days=today.weekday())
        else:
            try:
                week_start = date_cls.fromisoformat(week_start_str)
            except ValueError:
                return Response({'error': 'Invalid date format'}, status=status.HTTP_400_BAD_REQUEST)

        week_end = week_start + td(days=6)
        dates = [week_start + td(days=i) for i in range(7)]

        lpo_profiles = Profile.objects.filter(
            role='LPO', status='Active',
        ).select_related('user').order_by('user__first_name', 'user__last_name')

        avails = Availability.objects.filter(
            date__gte=week_start, date__lte=week_end,
            user__profile__role='LPO',
        ).select_related('user')

        avail_map = {}
        for a in avails:
            avail_map.setdefault(a.user_id, {})[str(a.date)] = AvailabilitySerializer(a).data

        users_data = []
        for profile in lpo_profiles:
            user = profile.user
            user_avails = avail_map.get(user.id, {})
            days = {}
            for d in dates:
                d_str = str(d)
                days[d_str] = user_avails.get(d_str, None)
            users_data.append({
                'user_id': user.id,
                'user_name': f'{user.first_name} {user.last_name}'.strip() or user.username,
                'days': days,
            })

        return Response({
            'week_start': str(week_start),
            'week_end': str(week_end),
            'dates': [str(d) for d in dates],
            'users': users_data,
        })

    # --- Quick-set availability for a user + date ---
    @action(detail=False, methods=['post'])
    def quick_set(self, request):
        """Set/update availability for a user + date using a preset."""
        user_id = request.data.get('user')
        date_val = request.data.get('date')
        preset = request.data.get('preset', 'custom')
        is_available = request.data.get('is_available', True)
        notes = request.data.get('notes', '')

        if not user_id or not date_val:
            return Response({'error': 'user and date required'}, status=status.HTTP_400_BAD_REQUEST)

        from .models import Availability as AvailModel
        PRESET_TIMES = AvailModel.PRESET_TIMES

        if preset in PRESET_TIMES:
            start_time, end_time = PRESET_TIMES[preset]
        else:
            start_time = request.data.get('start_time')
            end_time = request.data.get('end_time')
            if not start_time or not end_time:
                return Response(
                    {'error': 'start_time and end_time required for custom preset'},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        avail, created = Availability.objects.update_or_create(
            user_id=user_id,
            date=date_val,
            defaults={
                'preset': preset,
                'start_time': start_time,
                'end_time': end_time,
                'is_available': is_available,
                'notes': notes,
            },
        )

        return Response(
            AvailabilitySerializer(avail).data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )

    # --- Remove availability for a user + date ---
    @action(detail=False, methods=['post'])
    def remove_date(self, request):
        """Remove availability entry for a user + date."""
        user_id = request.data.get('user')
        date_val = request.data.get('date')
        if not user_id or not date_val:
            return Response({'error': 'user and date required'}, status=status.HTTP_400_BAD_REQUEST)
        deleted, _ = Availability.objects.filter(user_id=user_id, date=date_val).delete()
        return Response({'deleted': deleted})


# ===================================================================
# PTO Request ViewSet
# ===================================================================

class PTORequestViewSet(viewsets.ModelViewSet):
    serializer_class = PTORequestSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_class = PTORequestFilter
    search_fields = ['user__first_name', 'user__last_name']
    ordering_fields = ['start_date', 'created_at', 'status']

    def get_queryset(self):
        qs = PTORequest.objects.select_related('user', 'reviewed_by')
        user = self.request.user
        if hasattr(user, 'profile') and user.profile.role == 'LPO':
            qs = qs.filter(user=user)
        return qs

    def perform_create(self, serializer):
        pto = serializer.save()
        # Notify admins/managers
        from profiles.models import Profile
        admins = User.objects.filter(
            profile__role='Admin',
        ).exclude(pk=pto.user.pk)
        for admin in admins:
            _notify(
                admin, 'pto_request',
                'New PTO Request',
                f'{pto.user.get_full_name()} requested {pto.get_leave_type_display()} '
                f'from {pto.start_date} to {pto.end_date}.',
            )

    # --- Approve/Reject PTO ---
    @action(detail=True, methods=['post'])
    def review(self, request, pk=None):
        """Approve or reject a PTO request."""
        pto = self.get_object()
        new_status = request.data.get('status')  # 'approved' or 'rejected'
        if new_status not in ('approved', 'rejected'):
            return Response({'error': 'status must be approved or rejected'}, status=status.HTTP_400_BAD_REQUEST)

        pto.status = new_status
        pto.reviewed_by = request.user
        pto.reviewed_at = timezone.now()
        pto.notes = request.data.get('notes', pto.notes)
        pto.save()

        ntype = 'pto_approved' if new_status == 'approved' else 'pto_rejected'
        _notify(
            pto.user, ntype,
            f'PTO {new_status.title()}',
            f'Your {pto.get_leave_type_display()} request ({pto.start_date} to {pto.end_date}) '
            f'has been {new_status}.',
        )

        # If approved, cancel any conflicting shifts
        if new_status == 'approved':
            conflicting = RosterShift.objects.filter(
                user=pto.user,
                date__gte=pto.start_date,
                date__lte=pto.end_date,
                status__in=('scheduled', 'confirmed'),
            )
            for shift in conflicting:
                shift.status = 'cancelled'
                shift.notes = f'Auto-cancelled: PTO approved ({pto.get_leave_type_display()})'
                shift.save()
                _notify(
                    shift.user, 'shift_cancelled',
                    'Shift Cancelled',
                    f'Your shift on {shift.date} at {shift.branch.name} was cancelled due to approved leave.',
                    shift=shift,
                )

        return Response(PTORequestSerializer(pto).data)


# ===================================================================
# Drop Request ViewSet
# ===================================================================

class DropRequestViewSet(viewsets.ModelViewSet):
    serializer_class = DropRequestSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['status', 'requested_by']
    ordering_fields = ['created_at', 'status']

    def get_queryset(self):
        qs = DropRequest.objects.select_related(
            'shift', 'shift__branch', 'requested_by', 'reviewed_by',
        )
        user = self.request.user
        if hasattr(user, 'profile') and user.profile.role == 'LPO':
            qs = qs.filter(requested_by=user)
        return qs

    def perform_create(self, serializer):
        drop = serializer.save()
        # Notify admins
        from profiles.models import Profile
        admins = User.objects.filter(profile__role='Admin').exclude(pk=drop.requested_by.pk)
        for admin in admins:
            _notify(
                admin, 'drop_request',
                'New Drop Request',
                f'{drop.requested_by.get_full_name()} wants to drop their shift on '
                f'{drop.shift.date} at {drop.shift.branch.name}.',
                shift=drop.shift,
            )

    @action(detail=True, methods=['post'])
    def review(self, request, pk=None):
        """Approve or reject a drop request."""
        drop = self.get_object()
        new_status = request.data.get('status')
        if new_status not in ('approved', 'rejected'):
            return Response({'error': 'status must be approved or rejected'}, status=status.HTTP_400_BAD_REQUEST)

        drop.status = new_status
        drop.reviewed_by = request.user
        drop.reviewed_at = timezone.now()
        drop.save()

        ntype = 'drop_approved' if new_status == 'approved' else 'drop_rejected'
        _notify(
            drop.requested_by, ntype,
            f'Drop Request {new_status.title()}',
            f'Your request to drop the shift on {drop.shift.date} '
            f'at {drop.shift.branch.name} has been {new_status}.',
            shift=drop.shift,
        )

        if new_status == 'approved':
            drop.shift.status = 'cancelled'
            drop.shift.notes = 'Cancelled via approved drop request'
            drop.shift.save()

        return Response(DropRequestSerializer(drop).data)


# ===================================================================
# Notification ViewSet
# ===================================================================

class NotificationViewSet(viewsets.ModelViewSet):
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['notification_type', 'channel', 'is_read']
    ordering_fields = ['sent_at']

    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user)

    @action(detail=False, methods=['post'])
    def mark_all_read(self, request):
        """Mark all notifications as read for the current user."""
        count = Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
        return Response({'marked_read': count})

    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        """Mark a single notification as read."""
        notification = self.get_object()
        notification.is_read = True
        notification.save()
        return Response(NotificationSerializer(notification).data)

    @action(detail=False, methods=['get'])
    def unread_count(self, request):
        """Return count of unread notifications."""
        count = Notification.objects.filter(user=request.user, is_read=False).count()
        return Response({'count': count})
