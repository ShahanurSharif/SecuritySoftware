<script setup>
import { ref, computed, onMounted } from 'vue';
import { useToast } from 'primevue/usetoast';
import api from '@/services/api';

const toast = useToast();
const loading = ref(false);

// --- Data ---
const qrCodes = ref([]);
const totalRecords = ref(0);
const currentPage = ref(1);
const rowsPerPage = ref(10);
const sortField = ref('area_name');
const sortOrder = ref(1);
const filterText = ref('');

const branches = ref([]);
const companies = ref([]);

const qrDialog = ref(false);
const deleteDialog = ref(false);
const viewQRDialog = ref(false);
const isEditing = ref(false);
const submitted = ref(false);

const emptyQR = { id: null, branch: null, area_name: '', status: 'Active' };
const qr = ref({ ...emptyQR });
const selectedQR = ref(null);
const qrImageUrl = ref('');

// Company filter for branch select
const selectedCompany = ref(null);
const filteredBranches = computed(() => {
    if (!selectedCompany.value) return branches.value;
    return branches.value.filter((b) => b.company === selectedCompany.value);
});

// --- API field mapping ---
const apiSortMap = {
    area_name: 'area_name',
    company_name: 'branch__company__name',
    branch_name: 'branch__name',
    status: 'status',
    created_at: 'created_at'
};

// --- Fetch ---
const fetchQRCodes = async () => {
    loading.value = true;
    try {
        const params = { page: currentPage.value, page_size: rowsPerPage.value };
        if (filterText.value) params.search = filterText.value;
        const key = apiSortMap[sortField.value] || sortField.value;
        params.ordering = (sortOrder.value === -1 ? '-' : '') + key;

        const { data } = await api.get('/qrcodes/', { params });
        qrCodes.value = data.results;
        totalRecords.value = data.count;
    } catch {
        toast.add({ severity: 'error', summary: 'Error', detail: 'Failed to load QR codes.', life: 4000 });
    } finally {
        loading.value = false;
    }
};

const fetchBranches = async () => {
    try {
        const { data } = await api.get('/branches/', { params: { page_size: 1000 } });
        branches.value = data.results || data;
        // Extract unique companies
        const compMap = {};
        branches.value.forEach((b) => {
            compMap[b.company] = b.company_name;
        });
        companies.value = Object.entries(compMap).map(([id, name]) => ({ id: Number(id), name }));
    } catch {
        // silent
    }
};

onMounted(() => {
    fetchQRCodes();
    fetchBranches();
});

// --- Pagination / Sort / Search ---
const onPage = (event) => {
    currentPage.value = Math.floor(event.first / event.rows) + 1;
    rowsPerPage.value = event.rows;
    fetchQRCodes();
};

const onSort = (event) => {
    sortField.value = event.sortField;
    sortOrder.value = event.sortOrder;
    currentPage.value = 1;
    fetchQRCodes();
};

let searchTimeout = null;
const onSearch = () => {
    clearTimeout(searchTimeout);
    searchTimeout = setTimeout(() => {
        currentPage.value = 1;
        fetchQRCodes();
    }, 400);
};

// --- CRUD ---
const openNew = () => {
    qr.value = { ...emptyQR };
    selectedCompany.value = null;
    isEditing.value = false;
    submitted.value = false;
    qrDialog.value = true;
};

const editQR = (data) => {
    qr.value = { id: data.id, branch: data.branch, area_name: data.area_name, status: data.status };
    selectedCompany.value = data.company_id;
    isEditing.value = true;
    submitted.value = false;
    qrDialog.value = true;
};

const confirmDelete = (data) => {
    selectedQR.value = data;
    deleteDialog.value = true;
};

const saveQR = async () => {
    submitted.value = true;
    if (!qr.value.area_name.trim() || !qr.value.branch || !qr.value.status) return;

    try {
        if (isEditing.value) {
            await api.put(`/qrcodes/${qr.value.id}/`, {
                branch: qr.value.branch,
                area_name: qr.value.area_name,
                status: qr.value.status
            });
            toast.add({ severity: 'success', summary: 'Updated', detail: 'QR Code updated.', life: 3000 });
        } else {
            await api.post('/qrcodes/', {
                branch: qr.value.branch,
                area_name: qr.value.area_name,
                status: qr.value.status
            });
            toast.add({ severity: 'success', summary: 'Created', detail: 'QR Code created.', life: 3000 });
        }
        qrDialog.value = false;
        fetchQRCodes();
    } catch (err) {
        const msg = err.response?.data?.detail || err.response?.data?.area_name?.[0] || 'Failed to save.';
        toast.add({ severity: 'error', summary: 'Error', detail: msg, life: 4000 });
    }
};

const deleteQRConfirmed = async () => {
    try {
        await api.delete(`/qrcodes/${selectedQR.value.id}/`);
        toast.add({ severity: 'success', summary: 'Deleted', detail: 'QR Code deleted.', life: 3000 });
        deleteDialog.value = false;
        selectedQR.value = null;
        fetchQRCodes();
    } catch {
        toast.add({ severity: 'error', summary: 'Error', detail: 'Failed to delete.', life: 4000 });
    }
};

const getStatusSeverity = (status) => (status === 'Active' ? 'success' : 'secondary');

// --- View QR Code ---
const openViewQR = async (data) => {
    selectedQR.value = data;
    qrImageUrl.value = '';
    viewQRDialog.value = true;
    try {
        const { data: blob } = await api.get(`/qrcodes/${data.id}/image/`, { responseType: 'blob' });
        qrImageUrl.value = URL.createObjectURL(blob);
    } catch {
        toast.add({ severity: 'error', summary: 'Error', detail: 'Failed to load QR code image.', life: 4000 });
    }
};

const downloadQR = async () => {
    if (!selectedQR.value) return;
    try {
        const { data } = await api.get(`/qrcodes/${selectedQR.value.id}/image/`, { responseType: 'blob' });
        const url = URL.createObjectURL(data);
        const link = document.createElement('a');
        link.download = `${selectedQR.value.area_name}.png`;
        link.href = url;
        link.click();
        URL.revokeObjectURL(url);
    } catch {
        toast.add({ severity: 'error', summary: 'Error', detail: 'Failed to download QR code.', life: 4000 });
    }
};

const printQR = () => {
    if (!selectedQR.value) return;
    const imgUrl = qrImageUrl.value;
    const win = window.open('', '_blank');
    win.document.write(`
        <html>
        <head><title>QR Code — ${selectedQR.value.area_name}</title>
        <style>
            body { display: flex; flex-direction: column; align-items: center; justify-content: center; min-height: 100vh; margin: 0; font-family: Arial, sans-serif; }
            img { max-width: 400px; }
            h2 { margin-bottom: 4px; }
            p { color: #666; margin-top: 4px; }
        </style>
        </head>
        <body>
            <h2>${selectedQR.value.area_name}</h2>
            <p>${selectedQR.value.branch_name} — ${selectedQR.value.company_name}</p>
            <img src="${imgUrl}" alt="QR Code" onload="window.print()" />
        </body>
        </html>
    `);
    win.document.close();
};

const onCompanyChange = () => {
    qr.value.branch = null;
};
</script>

<template>
    <Toast />
    <div class="card">
        <div class="font-semibold text-xl mb-4">QR Code Management</div>

        <!-- Search -->
        <div class="mb-4">
            <IconField>
                <InputIcon class="pi pi-search" />
                <InputText v-model="filterText" placeholder="Search by area, branch, company..." class="w-full" @input="onSearch" />
            </IconField>
        </div>

        <DataTable
            :value="qrCodes"
            :paginator="true"
            :rows="rowsPerPage"
            :totalRecords="totalRecords"
            :lazy="true"
            :loading="loading"
            :rowsPerPageOptions="[10, 25, 50]"
            @page="onPage"
            @sort="onSort"
            dataKey="id"
            :rowHover="true"
            responsiveLayout="scroll"
        >
            <template #header>
                <div class="flex justify-between items-center">
                    <span class="text-xl text-surface-900 dark:text-surface-0 font-bold">QR Codes</span>
                    <Button label="Create QR Code" icon="pi pi-plus" size="small" @click="openNew" />
                </div>
            </template>
            <template #empty>No QR codes found.</template>

            <Column field="area_name" header="Area Name" sortable style="min-width: 14rem" />
            <Column field="company_name" header="Company" sortable style="min-width: 12rem" />
            <Column field="branch_name" header="Branch" sortable style="min-width: 12rem" />
            <Column field="status" header="Status" sortable style="min-width: 8rem">
                <template #body="{ data }">
                    <Tag :value="data.status" :severity="getStatusSeverity(data.status)" />
                </template>
            </Column>
            <Column field="created_at" header="Created" sortable style="min-width: 12rem">
                <template #body="{ data }">
                    {{ new Date(data.created_at).toLocaleDateString() }}
                </template>
            </Column>
            <Column header="QR" style="min-width: 6rem">
                <template #body="{ data }">
                    <Button icon="pi pi-qrcode" rounded outlined severity="info" size="small" @click="openViewQR(data)" v-tooltip.top="'View QR'" />
                </template>
            </Column>
            <Column header="Actions" style="min-width: 10rem">
                <template #body="{ data }">
                    <div class="flex gap-2">
                        <Button icon="pi pi-pencil" rounded outlined severity="info" size="small" @click="editQR(data)" />
                        <Button icon="pi pi-trash" rounded outlined severity="danger" size="small" @click="confirmDelete(data)" />
                    </div>
                </template>
            </Column>
        </DataTable>
    </div>

    <!-- Create / Edit Dialog -->
    <Dialog v-model:visible="qrDialog" :header="isEditing ? 'Edit QR Code' : 'Create QR Code'" :modal="true" :style="{ width: '550px' }">
        <form @submit.prevent="saveQR">
            <div class="flex flex-col gap-6 mt-4">
                <div class="flex flex-col gap-2">
                    <label class="font-medium">Area Name *</label>
                    <InputText v-model="qr.area_name" :invalid="submitted && !qr.area_name.trim()" placeholder="e.g. Freezer, Dry Food, Main Entrance" />
                    <small v-if="submitted && !qr.area_name.trim()" class="text-red-500">Area name is required.</small>
                </div>

                <div class="flex flex-col gap-2">
                    <label class="font-medium">Company *</label>
                    <Select v-model="selectedCompany" :options="companies" optionLabel="name" optionValue="id" placeholder="Select a company" @change="onCompanyChange" />
                </div>

                <div class="flex flex-col gap-2">
                    <label class="font-medium">Branch *</label>
                    <Select v-model="qr.branch" :options="filteredBranches" optionLabel="name" optionValue="id" placeholder="Select a branch" :invalid="submitted && !qr.branch" :disabled="!selectedCompany" />
                    <small v-if="submitted && !qr.branch" class="text-red-500">Branch is required.</small>
                </div>

                <div class="flex flex-col gap-2">
                    <label class="font-medium">Status *</label>
                    <Select v-model="qr.status" :options="['Active', 'Inactive']" placeholder="Select status" :invalid="submitted && !qr.status" />
                    <small v-if="submitted && !qr.status" class="text-red-500">Status is required.</small>
                </div>
            </div>

            <div class="flex justify-end gap-2 mt-6">
                <Button label="Cancel" icon="pi pi-times" severity="secondary" @click="qrDialog = false" type="button" />
                <Button type="submit" :label="isEditing ? 'Update' : 'Create'" icon="pi pi-check" />
            </div>
        </form>
    </Dialog>

    <!-- Delete Confirmation -->
    <Dialog v-model:visible="deleteDialog" header="Confirm Delete" :modal="true" :style="{ width: '400px' }">
        <div class="flex items-center gap-4">
            <i class="pi pi-exclamation-triangle text-3xl text-red-500" />
            <span>Are you sure you want to delete <strong>{{ selectedQR?.area_name }}</strong>?</span>
        </div>
        <template #footer>
            <div class="flex justify-end gap-2">
                <Button label="No" icon="pi pi-times" severity="secondary" @click="deleteDialog = false" />
                <Button label="Yes" icon="pi pi-check" severity="danger" @click="deleteQRConfirmed" />
            </div>
        </template>
    </Dialog>

    <!-- View QR Code Dialog -->
    <Dialog v-model:visible="viewQRDialog" header="QR Code" :modal="true" :style="{ width: '480px' }">
        <div v-if="selectedQR" class="flex flex-col items-center gap-4 py-4">
            <div class="text-center">
                <div class="text-xl font-semibold">{{ selectedQR.area_name }}</div>
                <div class="text-sm text-muted-color mt-1">{{ selectedQR.branch_name }} — {{ selectedQR.company_name }}</div>
            </div>

            <div v-if="qrImageUrl" class="bg-white p-4 rounded-xl shadow-sm">
                <img :src="qrImageUrl" alt="QR Code" class="w-64 h-64" />
            </div>
            <div v-else class="flex justify-center py-8">
                <ProgressSpinner style="width: 50px; height: 50px" />
            </div>
        </div>
        <template #footer>
            <div class="flex justify-end gap-2">
                <Button label="Print" icon="pi pi-print" severity="secondary" outlined @click="printQR" />
                <Button label="Download" icon="pi pi-download" severity="secondary" @click="downloadQR" />
                <Button label="Close" icon="pi pi-times" severity="secondary" @click="viewQRDialog = false" />
            </div>
        </template>
    </Dialog>
</template>
