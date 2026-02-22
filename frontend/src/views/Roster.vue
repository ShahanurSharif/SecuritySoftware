<script setup>
import { ref, computed, onMounted, watch } from 'vue';
import { useToast } from 'primevue/usetoast';
import api from '@/services/api';

const toast = useToast();

// ─── Active Tab ────────────────────────────────────────────────
const activeTab = ref(0);

// ─── Shared Lookups ────────────────────────────────────────────
const branches = ref([]);
const users = ref([]);
const shiftTemplates = ref([]);
const loading = ref(false);
const userRole = ref('Admin');

const fetchBranches = async () => {
    try {
        const { data } = await api.get('/branches/', { params: { page_size: 1000 } });
        branches.value = (data.results || data).map((b) => ({ label: b.name, value: b.id }));
    } catch {
        /* silent */
    }
};
const fetchUsers = async () => {
    try {
        const { data } = await api.get('/profiles/', { params: { page_size: 1000 } });
        users.value = (data.results || data).map((p) => ({
            label: `${p.user?.first_name || ''} ${p.user?.last_name || ''}`.trim() || p.user?.username,
            value: p.user?.id
        }));
    } catch {
        /* silent */
    }
};
const fetchTemplates = async () => {
    try {
        const { data } = await api.get('/roster/shift-templates/', { params: { page_size: 1000 } });
        shiftTemplates.value = data.results || data;
    } catch {
        /* silent */
    }
};
const fetchCurrentUser = async () => {
    try {
        const { data } = await api.get('/auth/me/');
        userRole.value = data.role;
    } catch {
        /* silent */
    }
};
const isAdmin = computed(() => userRole.value === 'Admin');

// ─── CALENDAR TAB ──────────────────────────────────────────────
const calendarMonth = ref(new Date().toISOString().slice(0, 7)); // YYYY-MM
const calendarShifts = ref([]);
const calendarLoading = ref(false);

const calendarDays = computed(() => {
    const [year, month] = calendarMonth.value.split('-').map(Number);
    const firstDay = new Date(year, month - 1, 1);
    const lastDay = new Date(year, month, 0);
    const startPad = firstDay.getDay() === 0 ? 6 : firstDay.getDay() - 1; // Monday start

    const days = [];
    // pad start
    for (let i = startPad; i > 0; i--) {
        const d = new Date(year, month - 1, 1 - i);
        days.push({ date: fmtDate(d), inMonth: false, shifts: [] });
    }
    // actual days
    for (let d = 1; d <= lastDay.getDate(); d++) {
        const dt = new Date(year, month - 1, d);
        const dateStr = fmtDate(dt);
        days.push({
            date: dateStr,
            inMonth: true,
            day: d,
            shifts: calendarShifts.value.filter((s) => s.date === dateStr)
        });
    }
    // pad end
    while (days.length % 7 !== 0) {
        const last = new Date(days[days.length - 1].date);
        last.setDate(last.getDate() + 1);
        days.push({ date: fmtDate(last), inMonth: false, shifts: [] });
    }
    return days;
});

const fmtDate = (d) => {
    const y = d.getFullYear();
    const m = String(d.getMonth() + 1).padStart(2, '0');
    const day = String(d.getDate()).padStart(2, '0');
    return `${y}-${m}-${day}`;
};

const today = computed(() => fmtDate(new Date()));

const fetchCalendarShifts = async () => {
    calendarLoading.value = true;
    try {
        const { data } = await api.get('/roster/shifts/calendar/', { params: { month: calendarMonth.value } });
        calendarShifts.value = data;
    } catch {
        toast.add({ severity: 'error', summary: 'Error', detail: 'Failed to load calendar shifts.', life: 4000 });
    } finally {
        calendarLoading.value = false;
    }
};

const prevMonth = () => {
    const [y, m] = calendarMonth.value.split('-').map(Number);
    const d = new Date(y, m - 2, 1);
    calendarMonth.value = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`;
};
const nextMonth = () => {
    const [y, m] = calendarMonth.value.split('-').map(Number);
    const d = new Date(y, m, 1);
    calendarMonth.value = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`;
};
const monthLabel = computed(() => {
    const [y, m] = calendarMonth.value.split('-').map(Number);
    return new Date(y, m - 1).toLocaleString('default', { month: 'long', year: 'numeric' });
});

watch(calendarMonth, fetchCalendarShifts);

const onCalendarDayClick = (day) => {
    if (!isAdmin.value) return;
    shiftForm.value = { ...emptyShift, date: day.date };
    shiftDialog.value = true;
};

// ─── SHIFTS TAB (CRUD) ────────────────────────────────────────
const shifts = ref([]);
const totalShifts = ref(0);
const shiftPage = ref(1);
const shiftRows = ref(10);
const shiftSortField = ref('date');
const shiftSortOrder = ref(-1);
const shiftsLoading = ref(false);

// Filters
const sfUser = ref(null);
const sfBranch = ref(null);
const sfStatus = ref(null);
const sfDateFrom = ref(null);
const sfDateTo = ref(null);

const shiftStatusOptions = [
    { label: 'Scheduled', value: 'scheduled' },
    { label: 'Confirmed', value: 'confirmed' },
    { label: 'Completed', value: 'completed' },
    { label: 'Cancelled', value: 'cancelled' },
    { label: 'No Show', value: 'no_show' }
];

const apiSortMap = { date: 'date', start_time: 'start_time', user_name: 'user', branch_name: 'branch', status: 'status' };

const fetchShifts = async () => {
    shiftsLoading.value = true;
    try {
        const params = {
            page: shiftPage.value,
            page_size: shiftRows.value
        };
        const sortKey = apiSortMap[shiftSortField.value] || shiftSortField.value;
        params.ordering = shiftSortOrder.value === 1 ? sortKey : `-${sortKey}`;
        if (sfUser.value) params.user = sfUser.value;
        if (sfBranch.value) params.branch = sfBranch.value;
        if (sfStatus.value) params.status = sfStatus.value;
        if (sfDateFrom.value) params.date_from = fmtDate(new Date(sfDateFrom.value));
        if (sfDateTo.value) params.date_to = fmtDate(new Date(sfDateTo.value));

        const { data } = await api.get('/roster/shifts/', { params });
        shifts.value = data.results || data;
        totalShifts.value = data.count ?? shifts.value.length;
    } catch {
        toast.add({ severity: 'error', summary: 'Error', detail: 'Failed to load shifts.', life: 4000 });
    } finally {
        shiftsLoading.value = false;
    }
};

const onShiftPage = (e) => {
    shiftPage.value = e.page + 1;
    shiftRows.value = e.rows;
    fetchShifts();
};
const onShiftSort = (e) => {
    shiftSortField.value = e.sortField;
    shiftSortOrder.value = e.sortOrder;
    fetchShifts();
};

let shiftFilterTimer = null;
const onShiftFilterChange = () => {
    clearTimeout(shiftFilterTimer);
    shiftFilterTimer = setTimeout(() => {
        shiftPage.value = 1;
        fetchShifts();
    }, 400);
};

const clearShiftFilters = () => {
    sfUser.value = null;
    sfBranch.value = null;
    sfStatus.value = null;
    sfDateFrom.value = null;
    sfDateTo.value = null;
    shiftPage.value = 1;
    fetchShifts();
};

// Shift Dialog
const shiftDialog = ref(false);
const deleteShiftDialog = ref(false);
const shiftSubmitted = ref(false);
const isEditingShift = ref(false);
const conflictWarning = ref(null);

const emptyShift = {
    id: null,
    user: null,
    branch: null,
    template: null,
    date: '',
    start_time: '',
    end_time: '',
    break_duration_minutes: 0,
    hourly_rate: 0,
    status: 'scheduled',
    notes: ''
};
const shiftForm = ref({ ...emptyShift });
const selectedShift = ref(null);

const openNewShift = () => {
    shiftForm.value = { ...emptyShift };
    isEditingShift.value = false;
    shiftSubmitted.value = false;
    conflictWarning.value = null;
    shiftDialog.value = true;
};

const editShift = (s) => {
    shiftForm.value = {
        id: s.id,
        user: s.user,
        branch: s.branch,
        template: s.template,
        date: s.date,
        start_time: s.start_time?.slice(0, 5) || '',
        end_time: s.end_time?.slice(0, 5) || '',
        break_duration_minutes: s.break_duration_minutes || 0,
        hourly_rate: s.hourly_rate || 0,
        status: s.status,
        notes: s.notes
    };
    isEditingShift.value = true;
    shiftSubmitted.value = false;
    conflictWarning.value = null;
    shiftDialog.value = true;
};

const applyTemplate = () => {
    const t = shiftTemplates.value.find((tpl) => tpl.id === shiftForm.value.template);
    if (t) {
        shiftForm.value.start_time = t.start_time?.slice(0, 5) || '';
        shiftForm.value.end_time = t.end_time?.slice(0, 5) || '';
        shiftForm.value.branch = t.branch;
        shiftForm.value.hourly_rate = t.hourly_rate || 0;
        shiftForm.value.break_duration_minutes = t.break_duration_minutes || 0;
    }
};

const checkConflicts = async () => {
    if (!shiftForm.value.user || !shiftForm.value.date || !shiftForm.value.start_time || !shiftForm.value.end_time) return;
    try {
        const { data } = await api.post('/roster/shifts/check_conflicts/', {
            user: shiftForm.value.user,
            date: shiftForm.value.date,
            start_time: shiftForm.value.start_time,
            end_time: shiftForm.value.end_time,
            exclude_id: shiftForm.value.id
        });
        if (data.has_shift_conflict || data.has_pto_conflict || data.has_availability_issue) {
            const warnings = [];
            if (data.has_shift_conflict) warnings.push('Overlapping shift exists');
            if (data.has_pto_conflict) warnings.push('User has approved PTO on this date');
            if (data.has_availability_issue) warnings.push('Outside user availability');
            conflictWarning.value = warnings.join(' | ');
        } else {
            conflictWarning.value = null;
        }
    } catch {
        /* silent */
    }
};

const saveShift = async () => {
    shiftSubmitted.value = true;
    if (!shiftForm.value.user || !shiftForm.value.branch || !shiftForm.value.date || !shiftForm.value.start_time || !shiftForm.value.end_time) return;

    try {
        const payload = {
            user: shiftForm.value.user,
            branch: shiftForm.value.branch,
            template: shiftForm.value.template || null,
            date: shiftForm.value.date,
            start_time: shiftForm.value.start_time,
            end_time: shiftForm.value.end_time,
            break_duration_minutes: shiftForm.value.break_duration_minutes || 0,
            hourly_rate: shiftForm.value.hourly_rate || 0,
            status: shiftForm.value.status,
            notes: shiftForm.value.notes
        };

        if (isEditingShift.value) {
            await api.put(`/roster/shifts/${shiftForm.value.id}/`, payload);
            toast.add({ severity: 'success', summary: 'Updated', detail: 'Shift updated.', life: 3000 });
        } else {
            await api.post('/roster/shifts/', payload);
            toast.add({ severity: 'success', summary: 'Created', detail: 'Shift created.', life: 3000 });
        }
        shiftDialog.value = false;
        fetchShifts();
        fetchCalendarShifts();
    } catch (err) {
        const detail = err.response?.data?.non_field_errors?.[0] || err.response?.data?.detail || 'Save failed.';
        toast.add({ severity: 'error', summary: 'Error', detail, life: 5000 });
    }
};

const confirmDeleteShift = (s) => {
    selectedShift.value = s;
    deleteShiftDialog.value = true;
};
const deleteShift = async () => {
    try {
        await api.delete(`/roster/shifts/${selectedShift.value.id}/`);
        toast.add({ severity: 'success', summary: 'Deleted', detail: 'Shift deleted.', life: 3000 });
        deleteShiftDialog.value = false;
        fetchShifts();
        fetchCalendarShifts();
    } catch {
        toast.add({ severity: 'error', summary: 'Error', detail: 'Delete failed.', life: 4000 });
    }
};

const statusSeverity = (st) => {
    const map = { scheduled: 'info', confirmed: 'success', completed: 'success', cancelled: 'danger', no_show: 'warn' };
    return map[st] || 'secondary';
};

// ─── COPY WEEK ─────────────────────────────────────────────────
const copyWeekDialog = ref(false);
const copySource = ref('');
const copyTarget = ref('');

const openCopyWeek = () => {
    copySource.value = '';
    copyTarget.value = '';
    copyWeekDialog.value = true;
};

const doCopyWeek = async () => {
    if (!copySource.value || !copyTarget.value) return;
    try {
        const { data } = await api.post('/roster/shifts/copy_week/', {
            source_week_start: fmtDate(new Date(copySource.value)),
            target_week_start: fmtDate(new Date(copyTarget.value))
        });
        toast.add({ severity: 'success', summary: 'Copied', detail: `${data.created} shifts copied.`, life: 3000 });
        copyWeekDialog.value = false;
        fetchShifts();
        fetchCalendarShifts();
    } catch {
        toast.add({ severity: 'error', summary: 'Error', detail: 'Copy failed.', life: 4000 });
    }
};

// ─── SHIFT TEMPLATES TAB ──────────────────────────────────────
const templates = ref([]);
const templatesLoading = ref(false);
const templateDialog = ref(false);
const deleteTemplateDialog = ref(false);
const templateSubmitted = ref(false);
const isEditingTemplate = ref(false);

const emptyTemplate = { id: null, name: '', start_time: '', end_time: '', branch: null, color: '#3B82F6', hourly_rate: 0, break_duration_minutes: 0, is_active: true };
const templateForm = ref({ ...emptyTemplate });
const selectedTemplate = ref(null);

const fetchAllTemplates = async () => {
    templatesLoading.value = true;
    try {
        const { data } = await api.get('/roster/shift-templates/', { params: { page_size: 1000 } });
        templates.value = data.results || data;
    } catch {
        toast.add({ severity: 'error', summary: 'Error', detail: 'Failed to load templates.', life: 4000 });
    } finally {
        templatesLoading.value = false;
    }
};

const openNewTemplate = () => {
    templateForm.value = { ...emptyTemplate };
    isEditingTemplate.value = false;
    templateSubmitted.value = false;
    templateDialog.value = true;
};
const editTemplate = (t) => {
    templateForm.value = {
        id: t.id,
        name: t.name,
        start_time: t.start_time?.slice(0, 5) || '',
        end_time: t.end_time?.slice(0, 5) || '',
        branch: t.branch,
        color: t.color,
        hourly_rate: t.hourly_rate || 0,
        break_duration_minutes: t.break_duration_minutes || 0,
        is_active: t.is_active
    };
    isEditingTemplate.value = true;
    templateSubmitted.value = false;
    templateDialog.value = true;
};
const saveTemplate = async () => {
    templateSubmitted.value = true;
    if (!templateForm.value.name || !templateForm.value.branch || !templateForm.value.start_time || !templateForm.value.end_time) return;
    try {
        const payload = { ...templateForm.value };
        if (isEditingTemplate.value) {
            await api.put(`/roster/shift-templates/${templateForm.value.id}/`, payload);
            toast.add({ severity: 'success', summary: 'Updated', detail: 'Template updated.', life: 3000 });
        } else {
            await api.post('/roster/shift-templates/', payload);
            toast.add({ severity: 'success', summary: 'Created', detail: 'Template created.', life: 3000 });
        }
        templateDialog.value = false;
        fetchAllTemplates();
        fetchTemplates();
    } catch (err) {
        const detail = err.response?.data?.name?.[0] || err.response?.data?.detail || 'Save failed.';
        toast.add({ severity: 'error', summary: 'Error', detail, life: 5000 });
    }
};
const confirmDeleteTemplate = (t) => {
    selectedTemplate.value = t;
    deleteTemplateDialog.value = true;
};
const deleteTemplate = async () => {
    try {
        await api.delete(`/roster/shift-templates/${selectedTemplate.value.id}/`);
        toast.add({ severity: 'success', summary: 'Deleted', detail: 'Template deleted.', life: 3000 });
        deleteTemplateDialog.value = false;
        fetchAllTemplates();
        fetchTemplates();
    } catch {
        toast.add({ severity: 'error', summary: 'Error', detail: 'Delete failed.', life: 4000 });
    }
};

// ─── AVAILABILITY TAB ──────────────────────────────────────────
const availabilities = ref([]);
const availLoading = ref(false);
const availDialog = ref(false);
const availSubmitted = ref(false);
const isEditingAvail = ref(false);
const deleteAvailDialog = ref(false);

const dayOptions = [
    { label: 'Monday', value: 0 },
    { label: 'Tuesday', value: 1 },
    { label: 'Wednesday', value: 2 },
    { label: 'Thursday', value: 3 },
    { label: 'Friday', value: 4 },
    { label: 'Saturday', value: 5 },
    { label: 'Sunday', value: 6 }
];

const emptyAvail = { id: null, user: null, day_of_week: null, start_time: '', end_time: '', is_available: true };
const availForm = ref({ ...emptyAvail });
const selectedAvail = ref(null);

const fetchAvailability = async () => {
    availLoading.value = true;
    try {
        const { data } = await api.get('/roster/availability/', { params: { page_size: 1000 } });
        availabilities.value = data.results || data;
    } catch {
        toast.add({ severity: 'error', summary: 'Error', detail: 'Failed to load availability.', life: 4000 });
    } finally {
        availLoading.value = false;
    }
};

const openNewAvail = () => {
    availForm.value = { ...emptyAvail };
    isEditingAvail.value = false;
    availSubmitted.value = false;
    availDialog.value = true;
};
const editAvail = (a) => {
    availForm.value = {
        id: a.id,
        user: a.user,
        day_of_week: a.day_of_week,
        start_time: a.start_time?.slice(0, 5) || '',
        end_time: a.end_time?.slice(0, 5) || '',
        is_available: a.is_available
    };
    isEditingAvail.value = true;
    availSubmitted.value = false;
    availDialog.value = true;
};
const saveAvail = async () => {
    availSubmitted.value = true;
    if (availForm.value.day_of_week === null || !availForm.value.start_time || !availForm.value.end_time) return;
    if (!isAdmin.value) availForm.value.user = null; // backend uses request.user
    try {
        const payload = { ...availForm.value };
        if (!payload.user) {
            // let the backend handle it
            const meRes = await api.get('/auth/me/');
            payload.user = meRes.data.id;
        }
        if (isEditingAvail.value) {
            await api.put(`/roster/availability/${availForm.value.id}/`, payload);
            toast.add({ severity: 'success', summary: 'Updated', detail: 'Availability updated.', life: 3000 });
        } else {
            await api.post('/roster/availability/', payload);
            toast.add({ severity: 'success', summary: 'Created', detail: 'Availability created.', life: 3000 });
        }
        availDialog.value = false;
        fetchAvailability();
    } catch (err) {
        const detail = err.response?.data?.detail || err.response?.data?.non_field_errors?.[0] || 'Save failed.';
        toast.add({ severity: 'error', summary: 'Error', detail, life: 5000 });
    }
};
const confirmDeleteAvail = (a) => {
    selectedAvail.value = a;
    deleteAvailDialog.value = true;
};
const deleteAvail = async () => {
    try {
        await api.delete(`/roster/availability/${selectedAvail.value.id}/`);
        toast.add({ severity: 'success', summary: 'Deleted', detail: 'Availability deleted.', life: 3000 });
        deleteAvailDialog.value = false;
        fetchAvailability();
    } catch {
        toast.add({ severity: 'error', summary: 'Error', detail: 'Delete failed.', life: 4000 });
    }
};

// ─── PTO TAB ───────────────────────────────────────────────────
const ptos = ref([]);
const ptoLoading = ref(false);
const ptoDialog = ref(false);
const ptoSubmitted = ref(false);
const ptoReviewDialog = ref(false);

const leaveTypeOptions = [
    { label: 'Annual Leave', value: 'annual' },
    { label: 'Sick Leave', value: 'sick' },
    { label: 'Personal Leave', value: 'personal' },
    { label: 'Unpaid Leave', value: 'unpaid' },
    { label: 'Other', value: 'other' }
];
const ptoStatusOptions = [
    { label: 'Pending', value: 'pending' },
    { label: 'Approved', value: 'approved' },
    { label: 'Rejected', value: 'rejected' },
    { label: 'Cancelled', value: 'cancelled' }
];

const emptyPTO = { id: null, user: null, leave_type: 'annual', start_date: null, end_date: null, reason: '' };
const ptoForm = ref({ ...emptyPTO });
const selectedPTO = ref(null);
const ptoReviewStatus = ref('approved');
const ptoReviewNotes = ref('');

const fetchPTOs = async () => {
    ptoLoading.value = true;
    try {
        const { data } = await api.get('/roster/pto/', { params: { page_size: 1000 } });
        ptos.value = data.results || data;
    } catch {
        toast.add({ severity: 'error', summary: 'Error', detail: 'Failed to load PTO requests.', life: 4000 });
    } finally {
        ptoLoading.value = false;
    }
};

const openNewPTO = () => {
    ptoForm.value = { ...emptyPTO };
    ptoSubmitted.value = false;
    ptoDialog.value = true;
};

const savePTO = async () => {
    ptoSubmitted.value = true;
    if (!ptoForm.value.leave_type || !ptoForm.value.start_date || !ptoForm.value.end_date) return;
    try {
        const payload = {
            leave_type: ptoForm.value.leave_type,
            start_date: fmtDate(new Date(ptoForm.value.start_date)),
            end_date: fmtDate(new Date(ptoForm.value.end_date)),
            reason: ptoForm.value.reason
        };
        // Get user id
        const meRes = await api.get('/auth/me/');
        payload.user = ptoForm.value.user || meRes.data.id;
        await api.post('/roster/pto/', payload);
        toast.add({ severity: 'success', summary: 'Submitted', detail: 'PTO request submitted.', life: 3000 });
        ptoDialog.value = false;
        fetchPTOs();
    } catch (err) {
        const detail = err.response?.data?.detail || err.response?.data?.non_field_errors?.[0] || 'Save failed.';
        toast.add({ severity: 'error', summary: 'Error', detail, life: 5000 });
    }
};

const openReviewPTO = (pto) => {
    selectedPTO.value = pto;
    ptoReviewStatus.value = 'approved';
    ptoReviewNotes.value = '';
    ptoReviewDialog.value = true;
};
const reviewPTO = async () => {
    try {
        await api.post(`/roster/pto/${selectedPTO.value.id}/review/`, {
            status: ptoReviewStatus.value,
            notes: ptoReviewNotes.value
        });
        toast.add({ severity: 'success', summary: 'Done', detail: `PTO ${ptoReviewStatus.value}.`, life: 3000 });
        ptoReviewDialog.value = false;
        fetchPTOs();
    } catch {
        toast.add({ severity: 'error', summary: 'Error', detail: 'Review failed.', life: 4000 });
    }
};

const ptoSeverity = (st) => {
    const map = { pending: 'warn', approved: 'success', rejected: 'danger', cancelled: 'secondary' };
    return map[st] || 'info';
};

// ─── DROP REQUESTS TAB ─────────────────────────────────────────
const drops = ref([]);
const dropsLoading = ref(false);
const dropDialog = ref(false);
const dropReviewDialog = ref(false);

const emptyDrop = { shift: null, reason: '' };
const dropForm = ref({ ...emptyDrop });
const selectedDrop = ref(null);
const dropReviewStatus = ref('approved');

// Get shifts available for drop (user's upcoming shifts)
const userShifts = ref([]);
const fetchUserShifts = async () => {
    try {
        const { data } = await api.get('/roster/shifts/', { params: { page_size: 1000, status: 'scheduled' } });
        userShifts.value = (data.results || data).map((s) => ({
            label: `${s.date} ${s.start_time?.slice(0, 5)}–${s.end_time?.slice(0, 5)} @ ${s.branch_name}`,
            value: s.id
        }));
    } catch {
        /* silent */
    }
};

const fetchDrops = async () => {
    dropsLoading.value = true;
    try {
        const { data } = await api.get('/roster/drop-requests/', { params: { page_size: 1000 } });
        drops.value = data.results || data;
    } catch {
        toast.add({ severity: 'error', summary: 'Error', detail: 'Failed to load drop requests.', life: 4000 });
    } finally {
        dropsLoading.value = false;
    }
};

const openNewDrop = () => {
    dropForm.value = { ...emptyDrop };
    fetchUserShifts();
    dropDialog.value = true;
};

const saveDrop = async () => {
    if (!dropForm.value.shift) return;
    try {
        await api.post('/roster/drop-requests/', {
            shift: dropForm.value.shift,
            reason: dropForm.value.reason
        });
        toast.add({ severity: 'success', summary: 'Submitted', detail: 'Drop request submitted.', life: 3000 });
        dropDialog.value = false;
        fetchDrops();
    } catch (err) {
        const detail = err.response?.data?.detail || 'Submit failed.';
        toast.add({ severity: 'error', summary: 'Error', detail, life: 5000 });
    }
};

const openReviewDrop = (d) => {
    selectedDrop.value = d;
    dropReviewStatus.value = 'approved';
    dropReviewDialog.value = true;
};
const reviewDrop = async () => {
    try {
        await api.post(`/roster/drop-requests/${selectedDrop.value.id}/review/`, { status: dropReviewStatus.value });
        toast.add({ severity: 'success', summary: 'Done', detail: `Drop request ${dropReviewStatus.value}.`, life: 3000 });
        dropReviewDialog.value = false;
        fetchDrops();
        fetchShifts();
        fetchCalendarShifts();
    } catch {
        toast.add({ severity: 'error', summary: 'Error', detail: 'Review failed.', life: 4000 });
    }
};

// ─── NOTIFICATIONS TAB ─────────────────────────────────────────
const notifications = ref([]);
const notiLoading = ref(false);
const unreadCount = ref(0);

// ─── WEEKLY SUMMARY ────────────────────────────────────────────
const weeklySummary = ref(null);
const weeklyLoading = ref(false);
const summaryWeekStart = ref('');

const getMonday = (d) => {
    const dt = new Date(d);
    const day = dt.getDay();
    const diff = dt.getDate() - day + (day === 0 ? -6 : 1);
    return fmtDate(new Date(dt.setDate(diff)));
};

const fetchWeeklySummary = async () => {
    const ws = summaryWeekStart.value;
    if (!ws) return;
    weeklyLoading.value = true;
    try {
        const { data } = await api.get('/roster/shifts/weekly_summary/', { params: { week_start: typeof ws === 'string' ? ws : fmtDate(new Date(ws)) } });
        weeklySummary.value = data;
    } catch {
        toast.add({ severity: 'error', summary: 'Error', detail: 'Failed to load weekly summary.', life: 4000 });
    } finally {
        weeklyLoading.value = false;
    }
};

// Computed: total hours for a calendar day
const dayTotalHours = (day) => {
    if (!day.shifts?.length) return 0;
    return day.shifts.reduce((sum, s) => sum + (s.total_hours || 0), 0).toFixed(1);
};

// Computed: total hours for the month
const monthTotalHours = computed(() => {
    return calendarShifts.value.reduce((sum, s) => sum + (s.total_hours || 0), 0).toFixed(1);
});
const monthTotalPay = computed(() => {
    return calendarShifts.value.reduce((sum, s) => sum + (s.total_pay || 0), 0).toFixed(2);
});

// Computed: calc hours from form times for preview
const formCalcHours = computed(() => {
    if (!shiftForm.value.start_time || !shiftForm.value.end_time) return null;
    const [sh, sm] = shiftForm.value.start_time.split(':').map(Number);
    const [eh, em] = shiftForm.value.end_time.split(':').map(Number);
    if (isNaN(sh) || isNaN(sm) || isNaN(eh) || isNaN(em)) return null;
    let diff = (eh * 60 + em) - (sh * 60 + sm);
    if (diff <= 0) diff += 24 * 60;
    const gross = diff / 60;
    const net = gross - (shiftForm.value.break_duration_minutes || 0) / 60;
    const pay = net * (shiftForm.value.hourly_rate || 0);
    return { gross: gross.toFixed(2), net: net.toFixed(2), pay: pay.toFixed(2) };
});

const fetchNotifications = async () => {
    notiLoading.value = true;
    try {
        const { data } = await api.get('/roster/notifications/', { params: { page_size: 100, ordering: '-sent_at' } });
        notifications.value = data.results || data;
    } catch {
        toast.add({ severity: 'error', summary: 'Error', detail: 'Failed to load notifications.', life: 4000 });
    } finally {
        notiLoading.value = false;
    }
};

const fetchUnreadCount = async () => {
    try {
        const { data } = await api.get('/roster/notifications/unread_count/');
        unreadCount.value = data.count;
    } catch {
        /* silent */
    }
};

const markRead = async (n) => {
    if (n.is_read) return;
    try {
        await api.post(`/roster/notifications/${n.id}/mark_read/`);
        n.is_read = true;
        unreadCount.value = Math.max(0, unreadCount.value - 1);
    } catch {
        /* silent */
    }
};

const markAllRead = async () => {
    try {
        await api.post('/roster/notifications/mark_all_read/');
        notifications.value.forEach((n) => (n.is_read = true));
        unreadCount.value = 0;
        toast.add({ severity: 'success', summary: 'Done', detail: 'All marked as read.', life: 3000 });
    } catch {
        toast.add({ severity: 'error', summary: 'Error', detail: 'Failed.', life: 4000 });
    }
};

// ─── INIT ──────────────────────────────────────────────────────
onMounted(async () => {
    await Promise.all([fetchCurrentUser(), fetchBranches(), fetchUsers(), fetchTemplates()]);
    fetchCalendarShifts();
    fetchShifts();
    fetchAllTemplates();
    fetchAvailability();
    fetchPTOs();
    fetchDrops();
    fetchNotifications();
    fetchUnreadCount();
});
</script>

<template>
    <div class="flex flex-col gap-4">
        <div class="font-semibold text-xl">Roster Management</div>

        <Tabs v-model:value="activeTab">
            <TabList>
                <Tab :value="0"><i class="pi pi-calendar mr-2"></i>Calendar</Tab>
                <Tab :value="1"><i class="pi pi-list mr-2"></i>Shifts</Tab>
                <Tab :value="2"><i class="pi pi-clock mr-2"></i>Templates</Tab>
                <Tab :value="3"><i class="pi pi-check-circle mr-2"></i>Availability</Tab>
                <Tab :value="4"><i class="pi pi-calendar-minus mr-2"></i>PTO</Tab>
                <Tab :value="5"><i class="pi pi-arrow-down mr-2"></i>Drop Requests</Tab>
                <Tab :value="6">
                    <i class="pi pi-bell mr-2"></i>Notifications
                    <Badge v-if="unreadCount > 0" :value="unreadCount" severity="danger" class="ml-2" />
                </Tab>
            </TabList>

            <TabPanels>
                <!-- ═══════ CALENDAR ═══════ -->
                <TabPanel :value="0">
                    <div class="card">
                        <div class="flex items-center justify-between mb-4">
                            <Button icon="pi pi-chevron-left" text rounded @click="prevMonth" />
                            <span class="text-lg font-bold">{{ monthLabel }}</span>
                            <Button icon="pi pi-chevron-right" text rounded @click="nextMonth" />
                        </div>

                        <ProgressBar v-if="calendarLoading" mode="indeterminate" class="mb-2" style="height: 3px" />

                        <!-- Month totals -->
                        <div class="flex gap-6 mb-3 text-sm">
                            <div class="flex items-center gap-2">
                                <i class="pi pi-clock text-primary"></i>
                                <span class="font-semibold">{{ monthTotalHours }}h</span>
                                <span class="text-muted-color">total hours</span>
                            </div>
                            <div class="flex items-center gap-2">
                                <i class="pi pi-dollar text-green-500"></i>
                                <span class="font-semibold">${{ monthTotalPay }}</span>
                                <span class="text-muted-color">total pay</span>
                            </div>
                            <div class="flex items-center gap-2">
                                <i class="pi pi-calendar text-blue-500"></i>
                                <span class="font-semibold">{{ calendarShifts.length }}</span>
                                <span class="text-muted-color">shifts</span>
                            </div>
                        </div>

                        <div class="grid grid-cols-7 gap-px bg-surface-200 dark:bg-surface-700 rounded-lg overflow-hidden">
                            <div v-for="d in ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']" :key="d" class="bg-surface-100 dark:bg-surface-800 text-center py-2 font-semibold text-sm">
                                {{ d }}
                            </div>
                            <div
                                v-for="(day, i) in calendarDays"
                                :key="i"
                                class="bg-surface-0 dark:bg-surface-900 min-h-24 p-1 cursor-pointer hover:bg-surface-50 dark:hover:bg-surface-800 transition-colors"
                                :class="{
                                    'opacity-40': !day.inMonth,
                                    'ring-2 ring-primary': day.date === today
                                }"
                                @click="onCalendarDayClick(day)"
                            >
                                <div class="text-xs font-medium mb-1" :class="day.date === today ? 'text-primary font-bold' : ''">
                                    {{ day.day }}
                                </div>
                                <div v-for="s in day.shifts?.slice(0, 3)" :key="s.id" class="text-xs rounded px-1 mb-0.5 truncate text-white" :style="{ backgroundColor: s.template_name ? '#3B82F6' : '#6B7280' }">
                                    {{ s.start_time?.slice(0, 5) }} {{ s.user_name?.split(' ')[0] }} <span class="opacity-75">{{ s.total_hours }}h</span>
                                </div>
                                <div v-if="day.shifts?.length > 3" class="text-xs text-muted-color">+{{ day.shifts.length - 3 }} more</div>
                                <div v-if="dayTotalHours(day) > 0" class="text-xs font-bold text-primary mt-0.5">{{ dayTotalHours(day) }}h</div>
                            </div>
                        </div>

                        <div v-if="isAdmin" class="flex gap-2 mt-4">
                            <Button label="Add Shift" icon="pi pi-plus" @click="openNewShift" />
                            <Button label="Copy Week" icon="pi pi-copy" severity="secondary" @click="openCopyWeek" />
                        </div>
                    </div>
                </TabPanel>

                <!-- ═══════ SHIFTS LIST ═══════ -->
                <TabPanel :value="1">
                    <div class="card">
                        <!-- Filters -->
                        <div class="grid grid-cols-1 md:grid-cols-5 gap-3 mb-4">
                            <Select v-if="isAdmin" v-model="sfUser" :options="users" optionLabel="label" optionValue="value" placeholder="All Users" showClear @change="onShiftFilterChange" />
                            <Select v-model="sfBranch" :options="branches" optionLabel="label" optionValue="value" placeholder="All Branches" showClear @change="onShiftFilterChange" />
                            <Select v-model="sfStatus" :options="shiftStatusOptions" optionLabel="label" optionValue="value" placeholder="All Status" showClear @change="onShiftFilterChange" />
                            <DatePicker v-model="sfDateFrom" placeholder="From" dateFormat="yy-mm-dd" showIcon @update:modelValue="onShiftFilterChange" />
                            <DatePicker v-model="sfDateTo" placeholder="To" dateFormat="yy-mm-dd" showIcon @update:modelValue="onShiftFilterChange" />
                        </div>
                        <div class="flex gap-2 mb-4">
                            <Button icon="pi pi-filter-slash" severity="secondary" text @click="clearShiftFilters" />
                            <Button v-if="isAdmin" label="New Shift" icon="pi pi-plus" @click="openNewShift" />
                        </div>

                        <DataTable
                            :value="shifts"
                            :loading="shiftsLoading"
                            :lazy="true"
                            :paginator="true"
                            :rows="shiftRows"
                            :totalRecords="totalShifts"
                            :rowsPerPageOptions="[10, 25, 50]"
                            :sortField="shiftSortField"
                            :sortOrder="shiftSortOrder"
                            @page="onShiftPage"
                            @sort="onShiftSort"
                            stripedRows
                            size="small"
                        >
                            <Column field="date" header="Date" sortable style="min-width: 7rem" />
                            <Column field="start_time" header="Start" sortable style="min-width: 5rem">
                                <template #body="{ data }">{{ data.start_time?.slice(0, 5) }}</template>
                            </Column>
                            <Column field="end_time" header="End" style="min-width: 5rem">
                                <template #body="{ data }">{{ data.end_time?.slice(0, 5) }}</template>
                            </Column>
                            <Column field="user_name" header="User" sortable style="min-width: 8rem" />
                            <Column field="branch_name" header="Branch" sortable style="min-width: 8rem" />
                            <Column field="total_hours" header="Hours" sortable style="min-width: 5rem">
                                <template #body="{ data }">
                                    <span class="font-semibold">{{ data.total_hours }}h</span>
                                </template>
                            </Column>
                            <Column field="hourly_rate" header="Rate" style="min-width: 4rem">
                                <template #body="{ data }">
                                    <span v-if="data.hourly_rate > 0">${{ Number(data.hourly_rate).toFixed(2) }}/h</span>
                                    <span v-else class="text-muted-color">—</span>
                                </template>
                            </Column>
                            <Column field="total_pay" header="Pay" style="min-width: 5rem">
                                <template #body="{ data }">
                                    <span v-if="data.total_pay > 0" class="font-semibold text-green-600">${{ data.total_pay.toFixed(2) }}</span>
                                    <span v-else class="text-muted-color">—</span>
                                </template>
                            </Column>
                            <Column field="status" header="Status" sortable style="min-width: 6rem">
                                <template #body="{ data }">
                                    <Tag :value="data.status_display" :severity="statusSeverity(data.status)" />
                                </template>
                            </Column>
                            <Column field="has_drop_request" header="Drop?" style="min-width: 4rem">
                                <template #body="{ data }">
                                    <i v-if="data.has_drop_request" class="pi pi-exclamation-triangle text-orange-500" title="Pending drop request"></i>
                                </template>
                            </Column>
                            <Column header="Actions" style="min-width: 8rem">
                                <template #body="{ data }">
                                    <div class="flex gap-1">
                                        <Button v-if="isAdmin" icon="pi pi-pencil" text rounded severity="info" @click="editShift(data)" />
                                        <Button v-if="isAdmin" icon="pi pi-trash" text rounded severity="danger" @click="confirmDeleteShift(data)" />
                                    </div>
                                </template>
                            </Column>
                            <template #empty>No shifts found.</template>
                        </DataTable>
                    </div>
                </TabPanel>

                <!-- ═══════ TEMPLATES ═══════ -->
                <TabPanel :value="2">
                    <div class="card">
                        <div class="flex justify-between items-center mb-4">
                            <span class="font-semibold text-lg">Shift Templates</span>
                            <Button v-if="isAdmin" label="New Template" icon="pi pi-plus" @click="openNewTemplate" />
                        </div>

                        <DataTable :value="templates" :loading="templatesLoading" stripedRows size="small">
                            <Column field="name" header="Name" sortable />
                            <Column field="branch_name" header="Branch" sortable />
                            <Column field="start_time" header="Start" sortable>
                                <template #body="{ data }">{{ data.start_time?.slice(0, 5) }}</template>
                            </Column>
                            <Column field="end_time" header="End">
                                <template #body="{ data }">{{ data.end_time?.slice(0, 5) }}</template>
                            </Column>
                            <Column field="color" header="Color" style="min-width: 4rem">
                                <template #body="{ data }">
                                    <div class="w-6 h-6 rounded" :style="{ backgroundColor: data.color }"></div>
                                </template>
                            </Column>
                            <Column field="net_hours" header="Net Hours" sortable style="min-width: 5rem">
                                <template #body="{ data }">
                                    <span class="font-semibold">{{ data.net_hours }}h</span>
                                </template>
                            </Column>
                            <Column field="hourly_rate" header="Rate" style="min-width: 5rem">
                                <template #body="{ data }">
                                    <span v-if="data.hourly_rate > 0">${{ Number(data.hourly_rate).toFixed(2) }}/h</span>
                                    <span v-else class="text-muted-color">—</span>
                                </template>
                            </Column>
                            <Column field="break_duration_minutes" header="Break" style="min-width: 4rem">
                                <template #body="{ data }">{{ data.break_duration_minutes }}min</template>
                            </Column>
                            <Column field="is_active" header="Active">
                                <template #body="{ data }">
                                    <Tag :value="data.is_active ? 'Active' : 'Inactive'" :severity="data.is_active ? 'success' : 'secondary'" />
                                </template>
                            </Column>
                            <Column v-if="isAdmin" header="Actions" style="min-width: 8rem">
                                <template #body="{ data }">
                                    <div class="flex gap-1">
                                        <Button icon="pi pi-pencil" text rounded severity="info" @click="editTemplate(data)" />
                                        <Button icon="pi pi-trash" text rounded severity="danger" @click="confirmDeleteTemplate(data)" />
                                    </div>
                                </template>
                            </Column>
                            <template #empty>No templates found.</template>
                        </DataTable>
                    </div>
                </TabPanel>

                <!-- ═══════ AVAILABILITY ═══════ -->
                <TabPanel :value="3">
                    <div class="card">
                        <div class="flex justify-between items-center mb-4">
                            <span class="font-semibold text-lg">Availability</span>
                            <Button label="Add Availability" icon="pi pi-plus" @click="openNewAvail" />
                        </div>

                        <DataTable :value="availabilities" :loading="availLoading" stripedRows size="small">
                            <Column field="user_name" header="User" sortable />
                            <Column field="day_display" header="Day" sortable />
                            <Column field="start_time" header="Start">
                                <template #body="{ data }">{{ data.start_time?.slice(0, 5) }}</template>
                            </Column>
                            <Column field="end_time" header="End">
                                <template #body="{ data }">{{ data.end_time?.slice(0, 5) }}</template>
                            </Column>
                            <Column field="is_available" header="Available">
                                <template #body="{ data }">
                                    <Tag :value="data.is_available ? 'Yes' : 'No'" :severity="data.is_available ? 'success' : 'danger'" />
                                </template>
                            </Column>
                            <Column header="Actions" style="min-width: 8rem">
                                <template #body="{ data }">
                                    <div class="flex gap-1">
                                        <Button icon="pi pi-pencil" text rounded severity="info" @click="editAvail(data)" />
                                        <Button icon="pi pi-trash" text rounded severity="danger" @click="confirmDeleteAvail(data)" />
                                    </div>
                                </template>
                            </Column>
                            <template #empty>No availability records.</template>
                        </DataTable>
                    </div>
                </TabPanel>

                <!-- ═══════ PTO ═══════ -->
                <TabPanel :value="4">
                    <div class="card">
                        <div class="flex justify-between items-center mb-4">
                            <span class="font-semibold text-lg">PTO / Leave Requests</span>
                            <Button label="New PTO Request" icon="pi pi-plus" @click="openNewPTO" />
                        </div>

                        <DataTable :value="ptos" :loading="ptoLoading" stripedRows size="small">
                            <Column field="user_name" header="User" sortable />
                            <Column field="type_display" header="Type" sortable />
                            <Column field="start_date" header="Start" sortable />
                            <Column field="end_date" header="End" />
                            <Column field="reason" header="Reason" style="max-width: 12rem">
                                <template #body="{ data }">
                                    <span class="truncate block max-w-48">{{ data.reason || '—' }}</span>
                                </template>
                            </Column>
                            <Column field="status" header="Status" sortable>
                                <template #body="{ data }">
                                    <Tag :value="data.status_display" :severity="ptoSeverity(data.status)" />
                                </template>
                            </Column>
                            <Column v-if="isAdmin" header="Actions" style="min-width: 6rem">
                                <template #body="{ data }">
                                    <Button v-if="data.status === 'pending'" label="Review" icon="pi pi-check" text size="small" @click="openReviewPTO(data)" />
                                </template>
                            </Column>
                            <template #empty>No PTO requests.</template>
                        </DataTable>
                    </div>
                </TabPanel>

                <!-- ═══════ DROP REQUESTS ═══════ -->
                <TabPanel :value="5">
                    <div class="card">
                        <div class="flex justify-between items-center mb-4">
                            <span class="font-semibold text-lg">Drop Requests</span>
                            <Button label="New Drop Request" icon="pi pi-plus" @click="openNewDrop" />
                        </div>

                        <DataTable :value="drops" :loading="dropsLoading" stripedRows size="small">
                            <Column header="Shift" style="min-width: 12rem">
                                <template #body="{ data }">
                                    {{ data.shift_detail?.date }} {{ data.shift_detail?.start_time?.slice(0, 5) }}–{{ data.shift_detail?.end_time?.slice(0, 5) }}
                                </template>
                            </Column>
                            <Column field="shift_detail.branch_name" header="Branch" />
                            <Column field="requested_by_name" header="Requested By" />
                            <Column field="reason" header="Reason" style="max-width: 12rem">
                                <template #body="{ data }">
                                    <span class="truncate block max-w-48">{{ data.reason || '—' }}</span>
                                </template>
                            </Column>
                            <Column field="status" header="Status">
                                <template #body="{ data }">
                                    <Tag :value="data.status_display" :severity="ptoSeverity(data.status)" />
                                </template>
                            </Column>
                            <Column v-if="isAdmin" header="Actions" style="min-width: 6rem">
                                <template #body="{ data }">
                                    <Button v-if="data.status === 'pending'" label="Review" icon="pi pi-check" text size="small" @click="openReviewDrop(data)" />
                                </template>
                            </Column>
                            <template #empty>No drop requests.</template>
                        </DataTable>
                    </div>
                </TabPanel>

                <!-- ═══════ NOTIFICATIONS ═══════ -->
                <TabPanel :value="6">
                    <div class="card">
                        <div class="flex justify-between items-center mb-4">
                            <span class="font-semibold text-lg">Notifications</span>
                            <Button v-if="unreadCount > 0" label="Mark All Read" icon="pi pi-check" severity="secondary" @click="markAllRead" />
                        </div>

                        <div v-if="notiLoading" class="text-center py-4">
                            <ProgressSpinner style="width: 40px; height: 40px" />
                        </div>

                        <div v-else-if="notifications.length === 0" class="text-center py-8 text-muted-color">No notifications.</div>

                        <div v-else class="flex flex-col gap-2">
                            <div
                                v-for="n in notifications"
                                :key="n.id"
                                class="flex items-start gap-3 p-3 rounded-lg border transition-colors cursor-pointer"
                                :class="n.is_read ? 'bg-surface-0 dark:bg-surface-900 border-surface-200 dark:border-surface-700' : 'bg-primary-50 dark:bg-primary-900/20 border-primary-200 dark:border-primary-700'"
                                @click="markRead(n)"
                            >
                                <i class="pi pi-bell mt-1" :class="n.is_read ? 'text-muted-color' : 'text-primary'"></i>
                                <div class="flex-1">
                                    <div class="font-semibold text-sm">{{ n.title }}</div>
                                    <div class="text-sm text-muted-color mt-0.5">{{ n.message }}</div>
                                    <div class="text-xs text-muted-color mt-1">{{ new Date(n.sent_at).toLocaleString() }}</div>
                                </div>
                                <Tag :value="n.type_display" size="small" />
                            </div>
                        </div>
                    </div>
                </TabPanel>
            </TabPanels>
        </Tabs>

        <!-- ═══════ SHIFT DIALOG ═══════ -->
        <Dialog v-model:visible="shiftDialog" :header="isEditingShift ? 'Edit Shift' : 'New Shift'" modal style="width: 32rem">
            <div class="flex flex-col gap-4">
                <Message v-if="conflictWarning" severity="warn" :closable="false">{{ conflictWarning }}</Message>

                <div class="flex flex-col gap-1">
                    <label class="font-semibold text-sm">User *</label>
                    <Select v-model="shiftForm.user" :options="users" optionLabel="label" optionValue="value" placeholder="Select User" :class="{ 'p-invalid': shiftSubmitted && !shiftForm.user }" @change="checkConflicts" filter />
                </div>
                <div class="flex flex-col gap-1">
                    <label class="font-semibold text-sm">Template</label>
                    <Select v-model="shiftForm.template" :options="shiftTemplates" optionLabel="name" optionValue="id" placeholder="(Optional) Apply template" showClear @change="applyTemplate" />
                </div>
                <div class="flex flex-col gap-1">
                    <label class="font-semibold text-sm">Branch *</label>
                    <Select v-model="shiftForm.branch" :options="branches" optionLabel="label" optionValue="value" placeholder="Select Branch" :class="{ 'p-invalid': shiftSubmitted && !shiftForm.branch }" filter />
                </div>
                <div class="flex flex-col gap-1">
                    <label class="font-semibold text-sm">Date *</label>
                    <DatePicker v-model="shiftForm.date" dateFormat="yy-mm-dd" :class="{ 'p-invalid': shiftSubmitted && !shiftForm.date }" @update:modelValue="checkConflicts" />
                </div>
                <div class="grid grid-cols-2 gap-3">
                    <div class="flex flex-col gap-1">
                        <label class="font-semibold text-sm">Start Time *</label>
                        <InputMask v-model="shiftForm.start_time" mask="99:99" placeholder="HH:MM" :class="{ 'p-invalid': shiftSubmitted && !shiftForm.start_time }" @complete="checkConflicts" />
                    </div>
                    <div class="flex flex-col gap-1">
                        <label class="font-semibold text-sm">End Time *</label>
                        <InputMask v-model="shiftForm.end_time" mask="99:99" placeholder="HH:MM" :class="{ 'p-invalid': shiftSubmitted && !shiftForm.end_time }" @complete="checkConflicts" />
                    </div>
                </div>
                <div class="grid grid-cols-2 gap-3">
                    <div class="flex flex-col gap-1">
                        <label class="font-semibold text-sm">Hourly Rate ($)</label>
                        <InputNumber v-model="shiftForm.hourly_rate" mode="currency" currency="USD" :minFractionDigits="2" :min="0" />
                    </div>
                    <div class="flex flex-col gap-1">
                        <label class="font-semibold text-sm">Break (minutes)</label>
                        <InputNumber v-model="shiftForm.break_duration_minutes" :min="0" suffix=" min" />
                    </div>
                </div>

                <!-- Calculated hours preview -->
                <div v-if="formCalcHours" class="bg-surface-100 dark:bg-surface-800 rounded-lg p-3 flex gap-6 text-sm">
                    <div><span class="text-muted-color">Gross:</span> <span class="font-semibold">{{ formCalcHours.gross }}h</span></div>
                    <div><span class="text-muted-color">Net:</span> <span class="font-bold text-primary">{{ formCalcHours.net }}h</span></div>
                    <div v-if="formCalcHours.pay > 0"><span class="text-muted-color">Pay:</span> <span class="font-bold text-green-600">${{ formCalcHours.pay }}</span></div>
                </div>

                <div v-if="isEditingShift" class="flex flex-col gap-1">
                    <label class="font-semibold text-sm">Status</label>
                    <Select v-model="shiftForm.status" :options="shiftStatusOptions" optionLabel="label" optionValue="value" />
                </div>
                <div class="flex flex-col gap-1">
                    <label class="font-semibold text-sm">Notes</label>
                    <Textarea v-model="shiftForm.notes" rows="2" autoResize />
                </div>
            </div>

            <template #footer>
                <Button label="Cancel" text @click="shiftDialog = false" />
                <Button :label="isEditingShift ? 'Update' : 'Create'" icon="pi pi-check" @click="saveShift" />
            </template>
        </Dialog>

        <!-- Delete Shift dialog -->
        <Dialog v-model:visible="deleteShiftDialog" header="Confirm Delete" modal style="width: 24rem">
            <p>Delete this shift?</p>
            <template #footer>
                <Button label="Cancel" text @click="deleteShiftDialog = false" />
                <Button label="Delete" icon="pi pi-trash" severity="danger" @click="deleteShift" />
            </template>
        </Dialog>

        <!-- Copy Week dialog -->
        <Dialog v-model:visible="copyWeekDialog" header="Copy Week" modal style="width: 28rem">
            <div class="flex flex-col gap-4">
                <div class="flex flex-col gap-1">
                    <label class="font-semibold text-sm">Source Week Start (Monday)</label>
                    <DatePicker v-model="copySource" dateFormat="yy-mm-dd" />
                </div>
                <div class="flex flex-col gap-1">
                    <label class="font-semibold text-sm">Target Week Start (Monday)</label>
                    <DatePicker v-model="copyTarget" dateFormat="yy-mm-dd" />
                </div>
            </div>
            <template #footer>
                <Button label="Cancel" text @click="copyWeekDialog = false" />
                <Button label="Copy" icon="pi pi-copy" @click="doCopyWeek" />
            </template>
        </Dialog>

        <!-- ═══════ TEMPLATE DIALOG ═══════ -->
        <Dialog v-model:visible="templateDialog" :header="isEditingTemplate ? 'Edit Template' : 'New Template'" modal style="width: 28rem">
            <div class="flex flex-col gap-4">
                <div class="flex flex-col gap-1">
                    <label class="font-semibold text-sm">Name *</label>
                    <InputText v-model="templateForm.name" :class="{ 'p-invalid': templateSubmitted && !templateForm.name }" />
                </div>
                <div class="flex flex-col gap-1">
                    <label class="font-semibold text-sm">Branch *</label>
                    <Select v-model="templateForm.branch" :options="branches" optionLabel="label" optionValue="value" placeholder="Select Branch" :class="{ 'p-invalid': templateSubmitted && !templateForm.branch }" filter />
                </div>
                <div class="grid grid-cols-2 gap-3">
                    <div class="flex flex-col gap-1">
                        <label class="font-semibold text-sm">Start Time *</label>
                        <InputMask v-model="templateForm.start_time" mask="99:99" placeholder="HH:MM" :class="{ 'p-invalid': templateSubmitted && !templateForm.start_time }" />
                    </div>
                    <div class="flex flex-col gap-1">
                        <label class="font-semibold text-sm">End Time *</label>
                        <InputMask v-model="templateForm.end_time" mask="99:99" placeholder="HH:MM" :class="{ 'p-invalid': templateSubmitted && !templateForm.end_time }" />
                    </div>
                </div>
                <div class="grid grid-cols-2 gap-3">
                    <div class="flex flex-col gap-1">
                        <label class="font-semibold text-sm">Hourly Rate ($)</label>
                        <InputNumber v-model="templateForm.hourly_rate" mode="currency" currency="USD" :minFractionDigits="2" :min="0" />
                    </div>
                    <div class="flex flex-col gap-1">
                        <label class="font-semibold text-sm">Break (minutes)</label>
                        <InputNumber v-model="templateForm.break_duration_minutes" :min="0" suffix=" min" />
                    </div>
                </div>
                <div class="flex flex-col gap-1">
                    <label class="font-semibold text-sm">Color</label>
                    <ColorPicker v-model="templateForm.color" />
                </div>
                <div class="flex items-center gap-2">
                    <ToggleSwitch v-model="templateForm.is_active" />
                    <label class="text-sm">Active</label>
                </div>
            </div>
            <template #footer>
                <Button label="Cancel" text @click="templateDialog = false" />
                <Button :label="isEditingTemplate ? 'Update' : 'Create'" icon="pi pi-check" @click="saveTemplate" />
            </template>
        </Dialog>

        <!-- Delete Template dialog -->
        <Dialog v-model:visible="deleteTemplateDialog" header="Confirm Delete" modal style="width: 24rem">
            <p>Delete this template?</p>
            <template #footer>
                <Button label="Cancel" text @click="deleteTemplateDialog = false" />
                <Button label="Delete" icon="pi pi-trash" severity="danger" @click="deleteTemplate" />
            </template>
        </Dialog>

        <!-- ═══════ AVAILABILITY DIALOG ═══════ -->
        <Dialog v-model:visible="availDialog" :header="isEditingAvail ? 'Edit Availability' : 'Add Availability'" modal style="width: 28rem">
            <div class="flex flex-col gap-4">
                <div v-if="isAdmin" class="flex flex-col gap-1">
                    <label class="font-semibold text-sm">User</label>
                    <Select v-model="availForm.user" :options="users" optionLabel="label" optionValue="value" placeholder="Select User" filter />
                </div>
                <div class="flex flex-col gap-1">
                    <label class="font-semibold text-sm">Day *</label>
                    <Select v-model="availForm.day_of_week" :options="dayOptions" optionLabel="label" optionValue="value" placeholder="Select Day" :class="{ 'p-invalid': availSubmitted && availForm.day_of_week === null }" />
                </div>
                <div class="grid grid-cols-2 gap-3">
                    <div class="flex flex-col gap-1">
                        <label class="font-semibold text-sm">Start Time *</label>
                        <InputMask v-model="availForm.start_time" mask="99:99" placeholder="HH:MM" :class="{ 'p-invalid': availSubmitted && !availForm.start_time }" />
                    </div>
                    <div class="flex flex-col gap-1">
                        <label class="font-semibold text-sm">End Time *</label>
                        <InputMask v-model="availForm.end_time" mask="99:99" placeholder="HH:MM" :class="{ 'p-invalid': availSubmitted && !availForm.end_time }" />
                    </div>
                </div>
                <div class="flex items-center gap-2">
                    <ToggleSwitch v-model="availForm.is_available" />
                    <label class="text-sm">Available</label>
                </div>
            </div>
            <template #footer>
                <Button label="Cancel" text @click="availDialog = false" />
                <Button :label="isEditingAvail ? 'Update' : 'Create'" icon="pi pi-check" @click="saveAvail" />
            </template>
        </Dialog>

        <!-- Delete Availability dialog -->
        <Dialog v-model:visible="deleteAvailDialog" header="Confirm Delete" modal style="width: 24rem">
            <p>Delete this availability record?</p>
            <template #footer>
                <Button label="Cancel" text @click="deleteAvailDialog = false" />
                <Button label="Delete" icon="pi pi-trash" severity="danger" @click="deleteAvail" />
            </template>
        </Dialog>

        <!-- ═══════ PTO DIALOG ═══════ -->
        <Dialog v-model:visible="ptoDialog" header="New PTO Request" modal style="width: 28rem">
            <div class="flex flex-col gap-4">
                <div v-if="isAdmin" class="flex flex-col gap-1">
                    <label class="font-semibold text-sm">User</label>
                    <Select v-model="ptoForm.user" :options="users" optionLabel="label" optionValue="value" placeholder="Select User (or self)" showClear filter />
                </div>
                <div class="flex flex-col gap-1">
                    <label class="font-semibold text-sm">Leave Type *</label>
                    <Select v-model="ptoForm.leave_type" :options="leaveTypeOptions" optionLabel="label" optionValue="value" :class="{ 'p-invalid': ptoSubmitted && !ptoForm.leave_type }" />
                </div>
                <div class="grid grid-cols-2 gap-3">
                    <div class="flex flex-col gap-1">
                        <label class="font-semibold text-sm">Start Date *</label>
                        <DatePicker v-model="ptoForm.start_date" dateFormat="yy-mm-dd" :class="{ 'p-invalid': ptoSubmitted && !ptoForm.start_date }" />
                    </div>
                    <div class="flex flex-col gap-1">
                        <label class="font-semibold text-sm">End Date *</label>
                        <DatePicker v-model="ptoForm.end_date" dateFormat="yy-mm-dd" :class="{ 'p-invalid': ptoSubmitted && !ptoForm.end_date }" />
                    </div>
                </div>
                <div class="flex flex-col gap-1">
                    <label class="font-semibold text-sm">Reason</label>
                    <Textarea v-model="ptoForm.reason" rows="2" autoResize />
                </div>
            </div>
            <template #footer>
                <Button label="Cancel" text @click="ptoDialog = false" />
                <Button label="Submit" icon="pi pi-check" @click="savePTO" />
            </template>
        </Dialog>

        <!-- PTO Review dialog -->
        <Dialog v-model:visible="ptoReviewDialog" header="Review PTO Request" modal style="width: 24rem">
            <div class="flex flex-col gap-4">
                <div>
                    <strong>{{ selectedPTO?.user_name }}</strong> — {{ selectedPTO?.type_display }}<br />
                    {{ selectedPTO?.start_date }} to {{ selectedPTO?.end_date }}
                </div>
                <div class="flex flex-col gap-1">
                    <label class="font-semibold text-sm">Decision</label>
                    <SelectButton v-model="ptoReviewStatus" :options="[{ label: 'Approve', value: 'approved' }, { label: 'Reject', value: 'rejected' }]" optionLabel="label" optionValue="value" />
                </div>
                <div class="flex flex-col gap-1">
                    <label class="font-semibold text-sm">Notes</label>
                    <Textarea v-model="ptoReviewNotes" rows="2" autoResize />
                </div>
            </div>
            <template #footer>
                <Button label="Cancel" text @click="ptoReviewDialog = false" />
                <Button label="Submit" icon="pi pi-check" @click="reviewPTO" />
            </template>
        </Dialog>

        <!-- ═══════ DROP REQUEST DIALOG ═══════ -->
        <Dialog v-model:visible="dropDialog" header="New Drop Request" modal style="width: 28rem">
            <div class="flex flex-col gap-4">
                <div class="flex flex-col gap-1">
                    <label class="font-semibold text-sm">Shift *</label>
                    <Select v-model="dropForm.shift" :options="userShifts" optionLabel="label" optionValue="value" placeholder="Select Shift" filter />
                </div>
                <div class="flex flex-col gap-1">
                    <label class="font-semibold text-sm">Reason</label>
                    <Textarea v-model="dropForm.reason" rows="2" autoResize />
                </div>
            </div>
            <template #footer>
                <Button label="Cancel" text @click="dropDialog = false" />
                <Button label="Submit" icon="pi pi-check" @click="saveDrop" />
            </template>
        </Dialog>

        <!-- Drop Review dialog -->
        <Dialog v-model:visible="dropReviewDialog" header="Review Drop Request" modal style="width: 24rem">
            <div class="flex flex-col gap-4">
                <div>
                    <strong>{{ selectedDrop?.requested_by_name }}</strong> wants to drop:<br />
                    {{ selectedDrop?.shift_detail?.date }} {{ selectedDrop?.shift_detail?.start_time?.slice(0, 5) }}–{{ selectedDrop?.shift_detail?.end_time?.slice(0, 5) }}
                    @ {{ selectedDrop?.shift_detail?.branch_name }}
                </div>
                <div v-if="selectedDrop?.reason" class="text-sm text-muted-color">Reason: {{ selectedDrop?.reason }}</div>
                <div class="flex flex-col gap-1">
                    <label class="font-semibold text-sm">Decision</label>
                    <SelectButton v-model="dropReviewStatus" :options="[{ label: 'Approve', value: 'approved' }, { label: 'Reject', value: 'rejected' }]" optionLabel="label" optionValue="value" />
                </div>
            </div>
            <template #footer>
                <Button label="Cancel" text @click="dropReviewDialog = false" />
                <Button label="Submit" icon="pi pi-check" @click="reviewDrop" />
            </template>
        </Dialog>
    </div>
</template>
