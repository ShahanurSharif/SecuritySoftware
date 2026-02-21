import re
import io
import pytesseract
from PIL import Image, ImageEnhance, ImageFilter
from django.db.models import Q
from django_filters import rest_framework as django_filters
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from branches.models import Branch
from .models import Attendance
from .serializers import AttendanceSerializer, AttendanceCreateSerializer


# ---------------------------------------------------------------------------
# Filters
# ---------------------------------------------------------------------------

class AttendanceFilter(django_filters.FilterSet):
    date_from = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='gte')
    date_to = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='lte')
    scanned_by = django_filters.NumberFilter(field_name='user')

    class Meta:
        model = Attendance
        fields = ['user', 'branch', 'type', 'method', 'status', 'scanned_by', 'date_from', 'date_to']


# ---------------------------------------------------------------------------
# OCR helpers — Humanforce POS screen extraction
# ---------------------------------------------------------------------------

# Time regex: H:MM:SS AM/PM or H:MM AM/PM (clock icon often OCR'd as © @ ® O)
_TIME_RE = re.compile(r'(\d{1,2}:\d{2}(?::\d{2})?\s*[AaPp][Mm])')
_TIME_24_RE = re.compile(r'(\d{1,2}:\d{2}(?::\d{2})?)')

# "Clocked In" / "Clocked Out" anchor — handles common OCR misreads:
#   Ciocked (i→l), Eiocked (E→Cl), Clockeg (g→d), Clockeqd (qd→d)
# Requires "e" after "ock" so "clocking on" is NOT matched.
_CLOCKED_RE = re.compile(
    r'[ce].{0,2}ocke\w{0,2}\s*(?:in|ou|o\W)',
    re.IGNORECASE,
)

# Words that should never be returned as branch names
_NOISE_WORDS = frozenset({
    'the', 'and', 'for', 'you', 'are', 'not', 'has', 'was', 'hrs',
    'exit', 'full', 'screen', 'press', 'hold', 'esc', 'psm', 'nmi',
    'rostered', 'anyone', 'found', 'breaks', 'before', 'after',
    'please', 'select', 'your', 'shift', 'details', 'below',
    'department', 'security', 'contractor', 'friday', 'saturday',
    'sunday', 'monday', 'tuesday', 'wednesday', 'thursday',
    'start', 'work', 'location', 'excessive', 'subject',
    'disciplinary', 'action', 'additional', 'minutes', 'hours',
    'awarded', 'worked', 'commencing', 'responsible', 'working',
    'notify', 'contacted', 'emergency', 'managers', 'unless',
    'information', 'message', 'call', 'limit', 'messages',
    'clock', 'clocked', 'clockeg', 'clockeqd', 'clocking',
    'ciocked', 'eiocked',
})


def _preprocess(img: Image.Image, scale: int = 2,
                contrast: float = 2.0, threshold: int = 130) -> Image.Image:
    """Grayscale → upscale → contrast → sharpen → binary threshold."""
    gray = img.convert('L')
    w, h = gray.size
    up = gray.resize((w * scale, h * scale), Image.LANCZOS)
    enh = ImageEnhance.Contrast(up).enhance(contrast)
    sharp = enh.filter(ImageFilter.SHARPEN)
    return sharp.point(lambda x: 255 if x > threshold else 0)


def _ocr_pass(img: Image.Image, psm: int = 6) -> str:
    """Run a single OCR pass and return text."""
    try:
        return pytesseract.image_to_string(img, config=f'--psm {psm}')
    except Exception:
        return ''


def _ocr_image(img: Image.Image) -> str:
    """
    Run multiple OCR strategies on a Humanforce POS attendance photo.
    Returns the combined text from all passes.
    """
    w, h = img.size
    results = []

    # --- Pass 1: Full image, moderate preprocessing ---
    full_proc = _preprocess(img, scale=2, contrast=2.0, threshold=130)
    results.append(_ocr_pass(full_proc, psm=6))

    # --- Pass 2: Top-left crop (portrait) for branch + status + time ---
    crop1 = img.crop((0, int(h * 0.03), int(w * 0.65), int(h * 0.45)))
    crop1_proc = _preprocess(crop1, scale=3, contrast=2.5, threshold=140)
    results.append(_ocr_pass(crop1_proc, psm=11))
    results.append(_ocr_pass(crop1_proc, psm=3))

    # --- Pass 3: Top half with aggressive contrast (for blurry photos) ---
    crop2 = img.crop((0, 0, w, int(h * 0.55)))
    crop2_proc = _preprocess(crop2, scale=3, contrast=3.0, threshold=120)
    results.append(_ocr_pass(crop2_proc, psm=6))

    # --- Pass 4: If landscape, try left half ---
    if w > h:
        crop3 = img.crop((0, 0, int(w * 0.55), h))
        crop3_proc = _preprocess(crop3, scale=2, contrast=2.5, threshold=130)
        results.append(_ocr_pass(crop3_proc, psm=6))

    # --- Pass 5: Centre card crop (for dark-wallpaper phones) ---
    crop4 = img.crop((int(w * 0.05), int(h * 0.2), int(w * 0.95), int(h * 0.65)))
    crop4_proc = _preprocess(crop4, scale=2, contrast=2.5, threshold=130)
    results.append(_ocr_pass(crop4_proc, psm=6))

    return '\n'.join(results)


def _clean_text(s: str) -> str:
    """Strip non-letter chars (except spaces) from a string."""
    return re.sub(r'[^A-Za-z\s]', '', s).strip()


def _is_good_branch(candidate: str) -> bool:
    """Return True if *candidate* looks like a plausible branch name."""
    if not candidate or len(candidate) < 4:
        return False
    words = candidate.split()
    # Branch names: 1-2 words, each ≥ 3 letters, no noise
    if len(words) > 2:
        return False
    for w in words:
        if len(w) < 3:
            return False
        if w.lower() in _NOISE_WORDS:
            return False
    # Reject words with implausible letter patterns — real place names
    # rarely have 4+ consecutive consonants or 3+ consecutive vowels
    text = candidate.replace(' ', '').upper()
    vowels = set('AEIOU')
    max_cons = max_vow = cur_cons = cur_vow = 0
    for ch in text:
        if ch in vowels:
            cur_vow += 1; cur_cons = 0
        else:
            cur_cons += 1; cur_vow = 0
        max_cons = max(max_cons, cur_cons)
        max_vow = max(max_vow, cur_vow)
    if max_cons > 4 or max_vow > 2:
        return False
    return True


def _best_word_from_line(line: str) -> str:
    """Extract the longest clean word (≥5 chars, not noise) from a line."""
    cleaned = _clean_text(line)
    words = cleaned.split()
    valid = [w for w in words if len(w) >= 5 and w.lower() not in _NOISE_WORDS]
    if valid:
        return max(valid, key=len)
    return ''


def _find_time_near_anchor(text: str) -> str:
    """
    Find the time that appears near/after a "Clocked In/Out" anchor line.
    On Humanforce POS, time is on the same line or the line just below.
    """
    lines = text.split('\n')
    for i, line in enumerate(lines):
        if _CLOCKED_RE.search(line):
            # Check current line for time
            m = _TIME_RE.search(line)
            if m:
                return m.group(1).strip()
            # Check lines below (up to 3)
            for j in range(i + 1, min(i + 4, len(lines))):
                m = _TIME_RE.search(lines[j])
                if m:
                    return m.group(1).strip()
                m24 = _TIME_24_RE.search(lines[j])
                if m24:
                    return m24.group(1).strip()
    return ''


def _extract_time(text: str) -> str:
    """Extract time from OCR text — prefer time near "Clocked" anchor."""
    # Strategy 1: Time near the "Clocked In/Out" anchor
    t = _find_time_near_anchor(text)
    if t:
        return t
    # Strategy 2: First AM/PM time anywhere in text
    m = _TIME_RE.search(text)
    if m:
        return m.group(1).strip()
    # Strategy 3: First 24h time
    m = _TIME_24_RE.search(text)
    if m:
        return m.group(1).strip()
    return ''


def _extract_branch(text: str) -> str:
    """
    Extract branch/location from Humanforce POS OCR text.

    Layout: branch name is bold text ABOVE "Clocked In/Out".
    Strategy: find ALL anchors, collect candidate branch above each,
    return the best (shortest single-word match preferred).
    """
    lines = [l.strip() for l in text.split('\n') if l.strip()]
    candidates = []

    # --- Strategy 1: Collect branch candidates above every anchor ---
    for i, line in enumerate(lines):
        if _CLOCKED_RE.search(line):
            for j in range(i - 1, max(i - 6, -1), -1):
                # Try full line first
                candidate = _clean_text(lines[j])
                if _is_good_branch(candidate):
                    candidates.append(candidate.upper())
                    break
                # Fallback: extract longest clean word from noisy line
                best = _best_word_from_line(lines[j])
                if best and len(best) >= 5 and _is_good_branch(best.upper()):
                    candidates.append(best.upper())
                    break

    # Dedup: if candidate A is a substring of candidate B, remove B
    # (B likely has OCR prefix/suffix noise, A is the real name)
    if len(candidates) > 1:
        to_keep = []
        for c in candidates:
            # Keep c only if no shorter candidate is a substring of c
            if not any(other in c and len(other) < len(c)
                       for other in candidates):
                to_keep.append(c)
        candidates = to_keep if to_keep else candidates

    # Prefer single-word, then LONGER (more complete branch names)
    if candidates:
        candidates.sort(key=lambda c: (len(c.split()), -len(c)))
        return candidates[0]

    # --- Strategy 2: "Location: <value>" keyword ---
    for line in lines:
        m = re.search(r'(?:location|branch|site)\s*[:\-]?\s*([A-Za-z]+)',
                       line, re.IGNORECASE)
        if m:
            val = m.group(1).strip()
            if _is_good_branch(val):
                return val.upper()

    # --- Strategy 3: First all-caps word ≥ 3 letters (not noise) ---
    for line in lines:
        cleaned = _clean_text(line)
        if cleaned and len(cleaned) >= 3 and cleaned.isupper():
            if _is_good_branch(cleaned):
                return cleaned

    return ''


# ---------------------------------------------------------------------------
# ViewSet
# ---------------------------------------------------------------------------

class AttendanceViewSet(viewsets.ModelViewSet):
    queryset = Attendance.objects.select_related('user', 'branch', 'branch__company').all()
    permission_classes = [permissions.IsAuthenticated]
    search_fields = ['user__first_name', 'user__last_name', 'branch__name', 'captured_branch']
    ordering_fields = ['created_at', 'type', 'method', 'status']
    ordering = ['-created_at']
    filterset_class = AttendanceFilter
    parser_classes = [MultiPartParser, FormParser]

    def get_serializer_class(self):
        if self.action in ('create', 'update', 'partial_update'):
            return AttendanceCreateSerializer
        return AttendanceSerializer

    # ------------------------------------------------------------------
    # OCR endpoint: POST /attendance/ocr/
    # Accepts an image, runs Tesseract OCR, returns extracted time & branch
    # ------------------------------------------------------------------
    @action(detail=False, methods=['post'], url_path='ocr')
    def ocr(self, request):
        """Extract time and branch name from an uploaded attendance photo."""
        file = request.FILES.get('image')
        if not file:
            return Response({'detail': 'No image provided.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            img = Image.open(io.BytesIO(file.read()))
        except Exception:
            return Response({'detail': 'Invalid image file.'}, status=status.HTTP_400_BAD_REQUEST)

        # Run OCR with image preprocessing pipeline
        try:
            raw_text = _ocr_image(img)
        except Exception as e:
            return Response(
                {'detail': f'OCR processing failed: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        extracted_time = _extract_time(raw_text)
        extracted_branch = _extract_branch(raw_text)

        return Response({
            'time': extracted_time,
            'branch_name': extracted_branch,
            'raw_text': raw_text,
        })

    # ------------------------------------------------------------------
    # Clock status: GET /attendance/clock-status/
    # Returns whether the current user is clocked in and the next type
    # ------------------------------------------------------------------
    @action(detail=False, methods=['get'], url_path='clock-status')
    def clock_status(self, request):
        """Return clock-in status for the current user."""
        last = (
            Attendance.objects
            .filter(user=request.user)
            .exclude(status='rejected')
            .order_by('-created_at')
            .first()
        )
        if last and last.type == 'clock_in':
            return Response({
                'is_clocked_in': True,
                'next_type': 'clock_out',
                'last_record': AttendanceSerializer(last).data,
            })
        return Response({
            'is_clocked_in': False,
            'next_type': 'clock_in',
            'last_record': AttendanceSerializer(last).data if last else None,
        })

    # ------------------------------------------------------------------
    # Camera submit: POST /attendance/submit/
    # Creates an attendance record from camera capture with OCR data
    # ------------------------------------------------------------------
    @action(detail=False, methods=['post'], url_path='submit')
    def submit(self, request):
        """Create an attendance record from camera capture."""
        user = request.user

        # Determine type based on last record
        last = (
            Attendance.objects
            .filter(user=user)
            .exclude(status='rejected')
            .order_by('-created_at')
            .first()
        )
        att_type = 'clock_out' if (last and last.type == 'clock_in') else 'clock_in'

        # Try to match branch by name
        branch = None
        branch_name = request.data.get('captured_branch', '')
        branch_id = request.data.get('branch')
        if branch_id:
            branch = Branch.objects.filter(id=branch_id).first()
        elif branch_name:
            branch = Branch.objects.filter(name__icontains=branch_name).first()

        attendance = Attendance.objects.create(
            user=user,
            branch=branch,
            type=att_type,
            captured_time=request.data.get('captured_time', ''),
            captured_branch=branch_name,
            image=request.FILES.get('image'),
            method='camera',
            status='approved',
        )
        return Response(AttendanceSerializer(attendance).data, status=status.HTTP_201_CREATED)

    # ------------------------------------------------------------------
    # Manual request: POST /attendance/manual/
    # Creates a pending manual attendance record for admin approval
    # ------------------------------------------------------------------
    @action(detail=False, methods=['post'], url_path='manual')
    def manual(self, request):
        """Create a manual attendance request (pending approval)."""
        user = request.user
        att_type = request.data.get('type', 'clock_in')
        branch_id = request.data.get('branch')
        branch = Branch.objects.filter(id=branch_id).first() if branch_id else None

        attendance = Attendance.objects.create(
            user=user,
            branch=branch,
            type=att_type,
            captured_time=request.data.get('captured_time', ''),
            method='manual',
            status='pending',
            reason=request.data.get('reason', ''),
        )
        return Response(AttendanceSerializer(attendance).data, status=status.HTTP_201_CREATED)
