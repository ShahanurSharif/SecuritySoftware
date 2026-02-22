<script setup>
import { ref, computed, onMounted } from 'vue';
import { useToast } from 'primevue/usetoast';
import api from '@/services/api';

const toast = useToast();

// ─── Lookups ───────────────────────────────────────────────────
const branches = ref([]);
const users = ref([]);

const fetchBranches = async () => {
    try {
        const { data } = await api.get('/branches/', { params: { page_size: 1000 } });
        branches.value = (data.results || data).map((b) => ({ label: b.name, value: b.id }));
    } catch { /* silent */ }
};

const fetchUsers = async () => {
    try {
        const { data } = await api.get('/profiles/', { params: { page_size: 1000 } });
        users.value = (data.results || data).map((p) => ({
            label: `${p.user?.first_name || ''} ${p.user?.last_name || ''}`.trim() || p.user?.username,
            value: p.user?.id
        }));
    } catch { /* silent */ }
};

// ─── List ──────────────────────────────────────────────────────
const reports = ref([]);
const totalReports = ref(0);
const page = ref(1);
const rows = ref(10);
const loading = ref(false);
const sortField = ref('incident_date');
const sortOrder = ref(-1);

// Filters
const fBranch = ref(null);
const fDateFrom = ref(null);
const fDateTo = ref(null);

const fmtDate = (d) => {
    const y = d.getFullYear();
    const m = String(d.getMonth() + 1).padStart(2, '0');
    const day = String(d.getDate()).padStart(2, '0');
    return `${y}-${m}-${day}`;
};

const apiSortMap = { incident_date: 'incident_date', incident_time: 'incident_time', amount_lost: 'amount_lost' };

const fetchReports = async () => {
    loading.value = true;
    try {
        const params = { page: page.value, page_size: rows.value };
        const sf = apiSortMap[sortField.value] || 'incident_date';
        params.ordering = sortOrder.value === 1 ? sf : `-${sf}`;
        if (fBranch.value) params.branch = fBranch.value;
        if (fDateFrom.value) params.date_from = fmtDate(new Date(fDateFrom.value));
        if (fDateTo.value) params.date_to = fmtDate(new Date(fDateTo.value));
        const { data } = await api.get('/reports/incidents/', { params });
        reports.value = data.results || data;
        totalReports.value = data.count ?? reports.value.length;
    } catch {
        toast.add({ severity: 'error', summary: 'Error', detail: 'Failed to load reports.', life: 4000 });
    } finally {
        loading.value = false;
    }
};

const onPage = (e) => { page.value = e.page + 1; rows.value = e.rows; fetchReports(); };
const onSort = (e) => { sortField.value = e.sortField; sortOrder.value = e.sortOrder; fetchReports(); };
let filterTimer = null;
const onFilterChange = () => { clearTimeout(filterTimer); filterTimer = setTimeout(() => { page.value = 1; fetchReports(); }, 400); };
const clearFilters = () => { fBranch.value = null; fDateFrom.value = null; fDateTo.value = null; page.value = 1; fetchReports(); };

// ─── Dialog ────────────────────────────────────────────────────
const dialog = ref(false);
const submitted = ref(false);
const isEditing = ref(false);
const deleteDialog = ref(false);
const selectedReport = ref(null);

const emptyForm = {
    id: null,
    branch: null,
    incident_date: null,
    incident_time: '',
    amount_lost: 0,
    amount_recovered: 0,
    damaged_items: '',
    description: '',
    police_intervention: false,
    injured: false
};
const form = ref({ ...emptyForm });

const netLoss = computed(() => {
    return Math.max(0, (Number(form.value.amount_lost) || 0) - (Number(form.value.amount_recovered) || 0));
});

const openNew = () => {
    form.value = { ...emptyForm, incident_date: new Date() };
    isEditing.value = false;
    submitted.value = false;
    dialog.value = true;
};

const editReport = (r) => {
    form.value = {
        id: r.id,
        branch: r.branch,
        incident_date: r.incident_date ? new Date(r.incident_date + 'T00:00:00') : null,
        incident_time: r.incident_time?.slice(0, 5) || '',
        amount_lost: Number(r.amount_lost) || 0,
        amount_recovered: Number(r.amount_recovered) || 0,
        damaged_items: r.damaged_items || '',
        description: r.description || '',
        police_intervention: r.police_intervention,
        injured: r.injured
    };
    isEditing.value = true;
    submitted.value = false;
    dialog.value = true;
};

const saveReport = async () => {
    submitted.value = true;
    if (!form.value.branch || !form.value.incident_date || !form.value.incident_time) return;
    try {
        const payload = {
            branch: form.value.branch,
            incident_date: fmtDate(new Date(form.value.incident_date)),
            incident_time: form.value.incident_time,
            amount_lost: form.value.amount_lost || 0,
            amount_recovered: form.value.amount_recovered || 0,
            damaged_items: form.value.damaged_items,
            description: form.value.description,
            police_intervention: form.value.police_intervention,
            injured: form.value.injured
        };
        if (isEditing.value) {
            await api.put(`/reports/incidents/${form.value.id}/`, payload);
            toast.add({ severity: 'success', summary: 'Updated', detail: 'Report updated.', life: 3000 });
        } else {
            await api.post('/reports/incidents/', payload);
            toast.add({ severity: 'success', summary: 'Created', detail: 'Incident report created.', life: 3000 });
        }
        dialog.value = false;
        fetchReports();
    } catch (err) {
        const detail = err.response?.data?.detail || err.response?.data?.non_field_errors?.[0] || 'Save failed.';
        toast.add({ severity: 'error', summary: 'Error', detail, life: 5000 });
    }
};

const confirmDelete = (r) => { selectedReport.value = r; deleteDialog.value = true; };
const deleteReport = async () => {
    try {
        await api.delete(`/reports/incidents/${selectedReport.value.id}/`);
        toast.add({ severity: 'success', summary: 'Deleted', detail: 'Report deleted.', life: 3000 });
        deleteDialog.value = false;
        fetchReports();
    } catch {
        toast.add({ severity: 'error', summary: 'Error', detail: 'Delete failed.', life: 4000 });
    }
};

// ─── Export as printable report ────────────────────────────────
const viewDialog = ref(false);
const viewReport = ref(null);

const openViewReport = (r) => {
    viewReport.value = r;
    viewDialog.value = true;
};

const printReport = () => {
    const r = viewReport.value;
    if (!r) return;
    const html = `
<!DOCTYPE html>
<html>
<head>
    <title>Incident Report #${r.id}</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 800px; margin: 40px auto; color: #333; }
        h1 { text-align: center; color: #1a1a2e; border-bottom: 3px solid #16213e; padding-bottom: 10px; }
        .meta { display: flex; justify-content: space-between; margin: 20px 0; background: #f5f5f5; padding: 15px; border-radius: 8px; }
        .meta div { text-align: center; }
        .meta .label { font-size: 11px; color: #666; text-transform: uppercase; letter-spacing: 1px; }
        .meta .value { font-size: 16px; font-weight: bold; margin-top: 4px; }
        .section { margin: 20px 0; }
        .section h3 { color: #16213e; border-bottom: 1px solid #ddd; padding-bottom: 5px; }
        .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin-top: 10px; }
        .field { background: #fafafa; padding: 12px; border-radius: 6px; border-left: 3px solid #3b82f6; }
        .field .label { font-size: 11px; color: #666; text-transform: uppercase; }
        .field .value { font-size: 18px; font-weight: bold; margin-top: 2px; }
        .field .value.loss { color: #dc2626; }
        .field .value.recovered { color: #16a34a; }
        .badge { display: inline-block; padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: bold; }
        .badge-yes { background: #fecaca; color: #dc2626; }
        .badge-no { background: #d1fae5; color: #16a34a; }
        .desc { background: #f5f5f5; padding: 15px; border-radius: 8px; line-height: 1.6; white-space: pre-wrap; }
        .footer { text-align: center; margin-top: 40px; font-size: 11px; color: #999; border-top: 1px solid #eee; padding-top: 10px; }
        @media print { body { margin: 20px; } }
    </style>
</head>
<body>
    <h1>Incident Report #${r.id}</h1>
    <div class="meta">
        <div><div class="label">Branch</div><div class="value">${r.branch_name || 'N/A'}</div></div>
        <div><div class="label">Date</div><div class="value">${r.incident_date}</div></div>
        <div><div class="label">Time</div><div class="value">${r.incident_time?.slice(0, 5) || 'N/A'}</div></div>
        <div><div class="label">Reported By</div><div class="value">${r.reported_by_name || 'N/A'}</div></div>
    </div>

    <div class="section">
        <h3>Financial Summary</h3>
        <div class="grid">
            <div class="field"><div class="label">Amount Lost</div><div class="value loss">$${Number(r.amount_lost).toFixed(2)}</div></div>
            <div class="field"><div class="label">Amount Recovered</div><div class="value recovered">$${Number(r.amount_recovered).toFixed(2)}</div></div>
            <div class="field"><div class="label">Net Loss</div><div class="value loss">$${Number(r.net_loss).toFixed(2)}</div></div>
        </div>
    </div>

    ${r.damaged_items ? `<div class="section"><h3>Damaged Items</h3><div class="desc">${r.damaged_items}</div></div>` : ''}

    ${r.description ? `<div class="section"><h3>Description</h3><div class="desc">${r.description}</div></div>` : ''}

    <div class="section">
        <h3>Additional Details</h3>
        <div class="grid">
            <div class="field">
                <div class="label">Police Intervention</div>
                <div class="value"><span class="badge ${r.police_intervention ? 'badge-yes' : 'badge-no'}">${r.police_intervention ? 'Yes' : 'No'}</span></div>
            </div>
            <div class="field">
                <div class="label">Injuries Reported</div>
                <div class="value"><span class="badge ${r.injured ? 'badge-yes' : 'badge-no'}">${r.injured ? 'Yes' : 'No'}</span></div>
            </div>
        </div>
    </div>

    <div class="footer">Generated on ${new Date().toLocaleString()} — Incident Report System</div>
</body>
</html>`;
    const w = window.open('', '_blank');
    w.document.write(html);
    w.document.close();
    w.focus();
    setTimeout(() => w.print(), 500);
};

// ─── Init ──────────────────────────────────────────────────────
onMounted(async () => {
    await Promise.all([fetchBranches(), fetchUsers(), fetchReports()]);
});
</script>

<template>
    <div class="flex flex-col gap-4">
        <div class="flex items-center justify-between">
            <div class="font-semibold text-xl">Incident Reports</div>
            <Button label="New Report" icon="pi pi-plus" @click="openNew" />
        </div>

        <!-- Filters -->
        <div class="card">
            <div class="grid grid-cols-1 md:grid-cols-4 gap-3 mb-3">
                <Select v-model="fBranch" :options="branches" optionLabel="label" optionValue="value" placeholder="All Branches" showClear @change="onFilterChange" />
                <DatePicker v-model="fDateFrom" placeholder="From Date" dateFormat="yy-mm-dd" showIcon @update:modelValue="onFilterChange" />
                <DatePicker v-model="fDateTo" placeholder="To Date" dateFormat="yy-mm-dd" showIcon @update:modelValue="onFilterChange" />
                <Button icon="pi pi-filter-slash" severity="secondary" text label="Clear" @click="clearFilters" />
            </div>

            <!-- Table -->
            <DataTable :value="reports" :loading="loading" :lazy="true" :paginator="true" :rows="rows" :totalRecords="totalReports" :rowsPerPageOptions="[10, 25, 50]" :sortField="sortField" :sortOrder="sortOrder" @page="onPage" @sort="onSort" stripedRows size="small">
                <Column field="incident_date" header="Date" sortable style="min-width: 7rem" />
                <Column field="incident_time" header="Time" style="min-width: 5rem">
                    <template #body="{ data }">{{ data.incident_time?.slice(0, 5) }}</template>
                </Column>
                <Column field="branch_name" header="Branch" style="min-width: 8rem" />
                <Column field="amount_lost" header="Lost" sortable style="min-width: 6rem">
                    <template #body="{ data }"><span class="text-red-600 font-semibold">${{ Number(data.amount_lost).toFixed(2) }}</span></template>
                </Column>
                <Column field="amount_recovered" header="Recovered" style="min-width: 6rem">
                    <template #body="{ data }"><span class="text-green-600 font-semibold">${{ Number(data.amount_recovered).toFixed(2) }}</span></template>
                </Column>
                <Column header="Net Loss" style="min-width: 6rem">
                    <template #body="{ data }"><span class="font-bold text-red-700">${{ Number(data.net_loss).toFixed(2) }}</span></template>
                </Column>
                <Column field="police_intervention" header="Police" style="min-width: 5rem">
                    <template #body="{ data }">
                        <Tag :value="data.police_intervention ? 'Yes' : 'No'" :severity="data.police_intervention ? 'danger' : 'success'" />
                    </template>
                </Column>
                <Column field="injured" header="Injured" style="min-width: 5rem">
                    <template #body="{ data }">
                        <Tag :value="data.injured ? 'Yes' : 'No'" :severity="data.injured ? 'danger' : 'success'" />
                    </template>
                </Column>
                <Column field="reported_by_name" header="Reported By" style="min-width: 8rem" />
                <Column header="Actions" style="min-width: 9rem">
                    <template #body="{ data }">
                        <div class="flex gap-1">
                            <Button icon="pi pi-eye" text rounded severity="info" v-tooltip="'View / Export'" @click="openViewReport(data)" />
                            <Button icon="pi pi-pencil" text rounded severity="info" @click="editReport(data)" />
                            <Button icon="pi pi-trash" text rounded severity="danger" @click="confirmDelete(data)" />
                        </div>
                    </template>
                </Column>
                <template #empty>No incident reports found.</template>
            </DataTable>
        </div>
    </div>

    <!-- ═══════ CREATE / EDIT DIALOG ═══════ -->
    <Dialog v-model:visible="dialog" :header="isEditing ? 'Edit Incident Report' : 'New Incident Report'" modal style="width: 36rem">
        <div class="flex flex-col gap-4">
            <!-- Branch -->
            <div class="flex flex-col gap-1">
                <label class="font-semibold text-sm">Branch / Store *</label>
                <Select v-model="form.branch" :options="branches" optionLabel="label" optionValue="value" placeholder="Select Branch" :class="{ 'p-invalid': submitted && !form.branch }" filter />
            </div>

            <!-- Date & Time -->
            <div class="grid grid-cols-2 gap-3">
                <div class="flex flex-col gap-1">
                    <label class="font-semibold text-sm">Date *</label>
                    <DatePicker v-model="form.incident_date" dateFormat="yy-mm-dd" :class="{ 'p-invalid': submitted && !form.incident_date }" showIcon />
                </div>
                <div class="flex flex-col gap-1">
                    <label class="font-semibold text-sm">Time *</label>
                    <InputMask v-model="form.incident_time" mask="99:99" placeholder="HH:MM" :class="{ 'p-invalid': submitted && !form.incident_time }" />
                </div>
            </div>

            <!-- Amounts -->
            <div class="grid grid-cols-2 gap-3">
                <div class="flex flex-col gap-1">
                    <label class="font-semibold text-sm">Amount Lost ($)</label>
                    <InputNumber v-model="form.amount_lost" mode="currency" currency="USD" :minFractionDigits="2" :min="0" />
                </div>
                <div class="flex flex-col gap-1">
                    <label class="font-semibold text-sm">Amount Recovered ($)</label>
                    <InputNumber v-model="form.amount_recovered" mode="currency" currency="USD" :minFractionDigits="2" :min="0" />
                </div>
            </div>

            <!-- Net Loss preview -->
            <div class="bg-surface-100 dark:bg-surface-800 rounded-lg p-3 flex items-center justify-between">
                <span class="text-sm text-muted-color">Net Loss</span>
                <span class="text-lg font-bold" :class="netLoss > 0 ? 'text-red-600' : 'text-green-600'">${{ netLoss.toFixed(2) }}</span>
            </div>

            <!-- Damaged Items -->
            <div class="flex flex-col gap-1">
                <label class="font-semibold text-sm">Damaged Items</label>
                <InputText v-model="form.damaged_items" placeholder="e.g. Display shelf, CCTV camera..." />
            </div>

            <!-- Description -->
            <div class="flex flex-col gap-1">
                <label class="font-semibold text-sm">Description</label>
                <Textarea v-model="form.description" rows="3" autoResize placeholder="Describe the incident..." />
            </div>

            <!-- Radio-style toggles -->
            <div class="grid grid-cols-2 gap-4">
                <div class="flex flex-col gap-2">
                    <label class="font-semibold text-sm">Police Intervention?</label>
                    <div class="flex gap-3">
                        <div class="flex items-center gap-2 cursor-pointer" @click="form.police_intervention = true">
                            <RadioButton v-model="form.police_intervention" :value="true" name="police" />
                            <label>Yes</label>
                        </div>
                        <div class="flex items-center gap-2 cursor-pointer" @click="form.police_intervention = false">
                            <RadioButton v-model="form.police_intervention" :value="false" name="police" />
                            <label>No</label>
                        </div>
                    </div>
                </div>
                <div class="flex flex-col gap-2">
                    <label class="font-semibold text-sm">Anyone Injured?</label>
                    <div class="flex gap-3">
                        <div class="flex items-center gap-2 cursor-pointer" @click="form.injured = true">
                            <RadioButton v-model="form.injured" :value="true" name="injured" />
                            <label>Yes</label>
                        </div>
                        <div class="flex items-center gap-2 cursor-pointer" @click="form.injured = false">
                            <RadioButton v-model="form.injured" :value="false" name="injured" />
                            <label>No</label>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <template #footer>
            <Button label="Cancel" text @click="dialog = false" />
            <Button :label="isEditing ? 'Update' : 'Submit Report'" icon="pi pi-check" @click="saveReport" />
        </template>
    </Dialog>

    <!-- ═══════ DELETE DIALOG ═══════ -->
    <Dialog v-model:visible="deleteDialog" header="Confirm Delete" modal style="width: 24rem">
        <p>Are you sure you want to delete this incident report?</p>
        <template #footer>
            <Button label="Cancel" text @click="deleteDialog = false" />
            <Button label="Delete" icon="pi pi-trash" severity="danger" @click="deleteReport" />
        </template>
    </Dialog>

    <!-- ═══════ VIEW / EXPORT DIALOG ═══════ -->
    <Dialog v-model:visible="viewDialog" header="Incident Report" modal style="width: 40rem">
        <div v-if="viewReport" class="flex flex-col gap-4">
            <!-- Header -->
            <div class="bg-surface-100 dark:bg-surface-800 rounded-lg p-4 flex justify-between items-start">
                <div>
                    <div class="text-lg font-bold">Incident #{{ viewReport.id }}</div>
                    <div class="text-sm text-muted-color">{{ viewReport.branch_name || 'N/A' }}</div>
                </div>
                <div class="text-right">
                    <div class="font-semibold">{{ viewReport.incident_date }}</div>
                    <div class="text-sm text-muted-color">{{ viewReport.incident_time?.slice(0, 5) }}</div>
                </div>
            </div>

            <!-- Financial -->
            <div class="grid grid-cols-3 gap-3">
                <div class="bg-red-50 dark:bg-red-900/20 rounded-lg p-3 text-center">
                    <div class="text-xs text-muted-color uppercase">Lost</div>
                    <div class="text-lg font-bold text-red-600">${{ Number(viewReport.amount_lost).toFixed(2) }}</div>
                </div>
                <div class="bg-green-50 dark:bg-green-900/20 rounded-lg p-3 text-center">
                    <div class="text-xs text-muted-color uppercase">Recovered</div>
                    <div class="text-lg font-bold text-green-600">${{ Number(viewReport.amount_recovered).toFixed(2) }}</div>
                </div>
                <div class="bg-orange-50 dark:bg-orange-900/20 rounded-lg p-3 text-center">
                    <div class="text-xs text-muted-color uppercase">Net Loss</div>
                    <div class="text-lg font-bold text-orange-600">${{ Number(viewReport.net_loss).toFixed(2) }}</div>
                </div>
            </div>

            <!-- Damaged Items -->
            <div v-if="viewReport.damaged_items" class="flex flex-col gap-1">
                <label class="font-semibold text-sm text-muted-color">Damaged Items</label>
                <div class="bg-surface-100 dark:bg-surface-800 rounded-lg p-3">{{ viewReport.damaged_items }}</div>
            </div>

            <!-- Description -->
            <div v-if="viewReport.description" class="flex flex-col gap-1">
                <label class="font-semibold text-sm text-muted-color">Description</label>
                <div class="bg-surface-100 dark:bg-surface-800 rounded-lg p-3 whitespace-pre-wrap">{{ viewReport.description }}</div>
            </div>

            <!-- Badges -->
            <div class="flex gap-4">
                <Tag :value="viewReport.police_intervention ? 'Police Involved' : 'No Police'" :severity="viewReport.police_intervention ? 'danger' : 'success'" icon="pi pi-shield" />
                <Tag :value="viewReport.injured ? 'Injuries Reported' : 'No Injuries'" :severity="viewReport.injured ? 'danger' : 'success'" icon="pi pi-heart" />
            </div>

            <!-- Reported By -->
            <div class="text-sm text-muted-color">
                Reported by <span class="font-semibold text-color">{{ viewReport.reported_by_name }}</span>
            </div>
        </div>

        <template #footer>
            <Button label="Close" text @click="viewDialog = false" />
            <Button label="Print / Export" icon="pi pi-print" @click="printReport" />
        </template>
    </Dialog>
</template>
