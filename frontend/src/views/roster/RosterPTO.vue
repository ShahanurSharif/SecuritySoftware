<script setup>
import { ref, onMounted } from 'vue';
import { useToast } from 'primevue/usetoast';
import api from '@/services/api';

const props = defineProps({
    users: Array,
    isAdmin: Boolean
});

const toast = useToast();

const fmtDate = (d) => {
    const y = d.getFullYear();
    const m = String(d.getMonth() + 1).padStart(2, '0');
    const day = String(d.getDate()).padStart(2, '0');
    return `${y}-${m}-${day}`;
};

// ─── State ─────────────────────────────────────────────────────
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

// ─── Fetch ─────────────────────────────────────────────────────
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

// ─── CRUD ──────────────────────────────────────────────────────
const openNewPTO = () => { ptoForm.value = { ...emptyPTO }; ptoSubmitted.value = false; ptoDialog.value = true; };

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

const openReviewPTO = (pto) => { selectedPTO.value = pto; ptoReviewStatus.value = 'approved'; ptoReviewNotes.value = ''; ptoReviewDialog.value = true; };
const reviewPTO = async () => {
    try {
        await api.post(`/roster/pto/${selectedPTO.value.id}/review/`, { status: ptoReviewStatus.value, notes: ptoReviewNotes.value });
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

const refresh = () => fetchPTOs();
defineExpose({ refresh });

onMounted(fetchPTOs);
</script>

<template>
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
                <template #body="{ data }"><span class="truncate block max-w-48">{{ data.reason || '—' }}</span></template>
            </Column>
            <Column field="status" header="Status" sortable>
                <template #body="{ data }"><Tag :value="data.status_display" :severity="ptoSeverity(data.status)" /></template>
            </Column>
            <Column v-if="isAdmin" header="Actions" style="min-width: 6rem">
                <template #body="{ data }">
                    <Button v-if="data.status === 'pending'" label="Review" icon="pi pi-check" text size="small" @click="openReviewPTO(data)" />
                </template>
            </Column>
            <template #empty>No PTO requests.</template>
        </DataTable>
    </div>

    <!-- PTO Dialog -->
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

    <!-- PTO Review -->
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
</template>
