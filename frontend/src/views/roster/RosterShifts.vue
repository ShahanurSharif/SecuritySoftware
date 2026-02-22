<script setup>
import { ref, computed, onMounted } from 'vue';
import { useToast } from 'primevue/usetoast';
import api from '@/services/api';

const props = defineProps({
    branches: Array,
    users: Array,
    shiftTemplates: Array,
    isAdmin: Boolean
});

const emit = defineEmits(['refresh-calendar', 'templates-updated']);
const toast = useToast();

const fmtDate = (d) => {
    const y = d.getFullYear();
    const m = String(d.getMonth() + 1).padStart(2, '0');
    const day = String(d.getDate()).padStart(2, '0');
    return `${y}-${m}-${day}`;
};

// ─── Shifts List ───────────────────────────────────────────────
const shifts = ref([]);
const totalShifts = ref(0);
const shiftPage = ref(1);
const shiftRows = ref(10);
const shiftSortField = ref('date');
const shiftSortOrder = ref(-1);
const shiftsLoading = ref(false);

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
        const params = { page: shiftPage.value, page_size: shiftRows.value };
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

const onShiftPage = (e) => { shiftPage.value = e.page + 1; shiftRows.value = e.rows; fetchShifts(); };
const onShiftSort = (e) => { shiftSortField.value = e.sortField; shiftSortOrder.value = e.sortOrder; fetchShifts(); };

let shiftFilterTimer = null;
const onShiftFilterChange = () => { clearTimeout(shiftFilterTimer); shiftFilterTimer = setTimeout(() => { shiftPage.value = 1; fetchShifts(); }, 400); };
const clearShiftFilters = () => { sfUser.value = null; sfBranch.value = null; sfStatus.value = null; sfDateFrom.value = null; sfDateTo.value = null; shiftPage.value = 1; fetchShifts(); };

const statusSeverity = (st) => {
    const map = { scheduled: 'info', confirmed: 'success', completed: 'success', cancelled: 'danger', no_show: 'warn' };
    return map[st] || 'secondary';
};

// ─── Shift Dialog ──────────────────────────────────────────────
const shiftDialog = ref(false);
const deleteShiftDialog = ref(false);
const shiftSubmitted = ref(false);
const isEditingShift = ref(false);
const conflictWarning = ref(null);
const selectedShift = ref(null);

const emptyShift = { id: null, user: null, branch: null, template: null, date: '', start_time: '', end_time: '', break_duration_minutes: 0, hourly_rate: 0, status: 'scheduled', notes: '' };
const shiftForm = ref({ ...emptyShift });

const openNewShift = (date) => {
    shiftForm.value = { ...emptyShift, date: date || '' };
    isEditingShift.value = false;
    shiftSubmitted.value = false;
    conflictWarning.value = null;
    shiftDialog.value = true;
};

const editShift = (s) => {
    shiftForm.value = {
        id: s.id, user: s.user, branch: s.branch, template: s.template,
        date: s.date, start_time: s.start_time?.slice(0, 5) || '', end_time: s.end_time?.slice(0, 5) || '',
        break_duration_minutes: s.break_duration_minutes || 0, hourly_rate: s.hourly_rate || 0,
        status: s.status, notes: s.notes
    };
    isEditingShift.value = true;
    shiftSubmitted.value = false;
    conflictWarning.value = null;
    shiftDialog.value = true;
};

const applyTemplate = () => {
    const t = props.shiftTemplates.find((tpl) => tpl.id === shiftForm.value.template);
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
            user: shiftForm.value.user, date: shiftForm.value.date,
            start_time: shiftForm.value.start_time, end_time: shiftForm.value.end_time,
            exclude_id: shiftForm.value.id
        });
        if (data.has_shift_conflict || data.has_pto_conflict || data.has_availability_issue) {
            const warnings = [];
            if (data.has_shift_conflict) warnings.push('Overlapping shift exists');
            if (data.has_pto_conflict) warnings.push('User has approved PTO on this date');
            if (data.has_availability_issue) warnings.push('Outside user availability');
            conflictWarning.value = warnings.join(' | ');
        } else { conflictWarning.value = null; }
    } catch { /* silent */ }
};

const saveShift = async () => {
    shiftSubmitted.value = true;
    if (!shiftForm.value.user || !shiftForm.value.branch || !shiftForm.value.date || !shiftForm.value.start_time || !shiftForm.value.end_time) return;
    try {
        const payload = {
            user: shiftForm.value.user, branch: shiftForm.value.branch, template: shiftForm.value.template || null,
            date: shiftForm.value.date, start_time: shiftForm.value.start_time, end_time: shiftForm.value.end_time,
            break_duration_minutes: shiftForm.value.break_duration_minutes || 0, hourly_rate: shiftForm.value.hourly_rate || 0,
            status: shiftForm.value.status, notes: shiftForm.value.notes
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
        emit('refresh-calendar');
    } catch (err) {
        const detail = err.response?.data?.non_field_errors?.[0] || err.response?.data?.detail || 'Save failed.';
        toast.add({ severity: 'error', summary: 'Error', detail, life: 5000 });
    }
};

const confirmDeleteShift = (s) => { selectedShift.value = s; deleteShiftDialog.value = true; };
const deleteShift = async () => {
    try {
        await api.delete(`/roster/shifts/${selectedShift.value.id}/`);
        toast.add({ severity: 'success', summary: 'Deleted', detail: 'Shift deleted.', life: 3000 });
        deleteShiftDialog.value = false;
        fetchShifts();
        emit('refresh-calendar');
    } catch {
        toast.add({ severity: 'error', summary: 'Error', detail: 'Delete failed.', life: 4000 });
    }
};

// ─── Copy Week ─────────────────────────────────────────────────
const copyWeekDialog = ref(false);
const copySource = ref('');
const copyTarget = ref('');

const openCopyWeek = () => { copySource.value = ''; copyTarget.value = ''; copyWeekDialog.value = true; };
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
        emit('refresh-calendar');
    } catch {
        toast.add({ severity: 'error', summary: 'Error', detail: 'Copy failed.', life: 4000 });
    }
};

// ─── Form calc ─────────────────────────────────────────────────
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

const refresh = () => fetchShifts();
defineExpose({ refresh, openNewShift, openCopyWeek });

onMounted(fetchShifts);
</script>

<template>
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
            <Button v-if="isAdmin" label="New Shift" icon="pi pi-plus" @click="openNewShift('')" />
        </div>

        <DataTable :value="shifts" :loading="shiftsLoading" :lazy="true" :paginator="true" :rows="shiftRows" :totalRecords="totalShifts" :rowsPerPageOptions="[10, 25, 50]" :sortField="shiftSortField" :sortOrder="shiftSortOrder" @page="onShiftPage" @sort="onShiftSort" stripedRows size="small">
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
                <template #body="{ data }"><span class="font-semibold">{{ data.total_hours }}h</span></template>
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
                <template #body="{ data }"><Tag :value="data.status_display" :severity="statusSeverity(data.status)" /></template>
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

    <!-- Delete Shift -->
    <Dialog v-model:visible="deleteShiftDialog" header="Confirm Delete" modal style="width: 24rem">
        <p>Delete this shift?</p>
        <template #footer>
            <Button label="Cancel" text @click="deleteShiftDialog = false" />
            <Button label="Delete" icon="pi pi-trash" severity="danger" @click="deleteShift" />
        </template>
    </Dialog>

    <!-- Copy Week -->
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
</template>
