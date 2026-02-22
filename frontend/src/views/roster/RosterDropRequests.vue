<script setup>
import { ref, onMounted } from 'vue';
import { useToast } from 'primevue/usetoast';
import api from '@/services/api';

const props = defineProps({
    isAdmin: Boolean
});

const toast = useToast();

// ─── State ─────────────────────────────────────────────────────
const drops = ref([]);
const dropsLoading = ref(false);
const dropDialog = ref(false);
const dropReviewDialog = ref(false);
const selectedDrop = ref(null);
const dropReviewStatus = ref('approved');

const emptyDrop = { shift: null, reason: '' };
const dropForm = ref({ ...emptyDrop });
const userShifts = ref([]);

// ─── Fetch ─────────────────────────────────────────────────────
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

const fetchUserShifts = async () => {
    try {
        const { data } = await api.get('/roster/shifts/', { params: { page_size: 1000, status: 'scheduled' } });
        userShifts.value = (data.results || data).map((s) => ({
            label: `${s.date} ${s.start_time?.slice(0, 5)}–${s.end_time?.slice(0, 5)} @ ${s.branch_name}`,
            value: s.id
        }));
    } catch { /* silent */ }
};

// ─── CRUD ──────────────────────────────────────────────────────
const openNewDrop = () => { dropForm.value = { ...emptyDrop }; fetchUserShifts(); dropDialog.value = true; };

const saveDrop = async () => {
    if (!dropForm.value.shift) return;
    try {
        await api.post('/roster/drop-requests/', { shift: dropForm.value.shift, reason: dropForm.value.reason });
        toast.add({ severity: 'success', summary: 'Submitted', detail: 'Drop request submitted.', life: 3000 });
        dropDialog.value = false;
        fetchDrops();
    } catch (err) {
        const detail = err.response?.data?.detail || 'Submit failed.';
        toast.add({ severity: 'error', summary: 'Error', detail, life: 5000 });
    }
};

const openReviewDrop = (d) => { selectedDrop.value = d; dropReviewStatus.value = 'approved'; dropReviewDialog.value = true; };
const reviewDrop = async () => {
    try {
        await api.post(`/roster/drop-requests/${selectedDrop.value.id}/review/`, { status: dropReviewStatus.value });
        toast.add({ severity: 'success', summary: 'Done', detail: `Drop request ${dropReviewStatus.value}.`, life: 3000 });
        dropReviewDialog.value = false;
        fetchDrops();
    } catch {
        toast.add({ severity: 'error', summary: 'Error', detail: 'Review failed.', life: 4000 });
    }
};

const ptoSeverity = (st) => {
    const map = { pending: 'warn', approved: 'success', rejected: 'danger', cancelled: 'secondary' };
    return map[st] || 'info';
};

const refresh = () => fetchDrops();
defineExpose({ refresh });

onMounted(fetchDrops);
</script>

<template>
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
                <template #body="{ data }"><span class="truncate block max-w-48">{{ data.reason || '—' }}</span></template>
            </Column>
            <Column field="status" header="Status">
                <template #body="{ data }"><Tag :value="data.status_display" :severity="ptoSeverity(data.status)" /></template>
            </Column>
            <Column v-if="isAdmin" header="Actions" style="min-width: 6rem">
                <template #body="{ data }">
                    <Button v-if="data.status === 'pending'" label="Review" icon="pi pi-check" text size="small" @click="openReviewDrop(data)" />
                </template>
            </Column>
            <template #empty>No drop requests.</template>
        </DataTable>
    </div>

    <!-- Drop Dialog -->
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

    <!-- Drop Review -->
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
</template>
