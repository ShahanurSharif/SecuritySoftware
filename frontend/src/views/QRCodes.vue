<script setup>
import { ref, computed } from 'vue';
import { useToast } from 'primevue/usetoast';

const toast = useToast();

const companies = ref([
    { id: 1, name: 'SecureCorp Ltd.' },
    { id: 2, name: 'CyberShield Inc.' }
]);

const branches = ref([
    { id: 1, companyId: 1, name: 'Downtown Branch' },
    { id: 2, companyId: 2, name: 'Bay Area Office' }
]);

const qrCodes = ref([
    { id: 1, name: 'Main Entrance', location: 'Building A — Front Door', companyId: 1, companyName: 'SecureCorp Ltd.', branchId: 1, branchName: 'Downtown Branch', createdAt: '2026-02-01 09:00:00', status: 'Active' },
    { id: 2, name: 'Parking Level 1', location: 'Building A — Basement P1', companyId: 1, companyName: 'SecureCorp Ltd.', branchId: 1, branchName: 'Downtown Branch', createdAt: '2026-02-01 09:15:00', status: 'Active' },
    { id: 3, name: 'Server Room', location: 'Building B — Floor 3', companyId: 2, companyName: 'CyberShield Inc.', branchId: 2, branchName: 'Bay Area Office', createdAt: '2026-02-05 14:30:00', status: 'Active' },
    { id: 4, name: 'Emergency Exit North', location: 'Building A — North Wing', companyId: 1, companyName: 'SecureCorp Ltd.', branchId: 1, branchName: 'Downtown Branch', createdAt: '2026-02-07 11:00:00', status: 'Inactive' }
]);

const qrDialog = ref(false);
const deleteDialog = ref(false);
const isEditing = ref(false);
const submitted = ref(false);
const filterText = ref('');

const filteredBranchOptions = computed(() => {
    if (!qr.value.companyId) return [];
    return branches.value.filter((b) => b.companyId === qr.value.companyId);
});

const onCompanyChange = () => {
    qr.value.branchId = null;
    qr.value.branchName = '';
};

const emptyQR = { id: null, name: '', location: '', companyId: null, companyName: '', branchId: null, branchName: '', status: 'Active' };
const qr = ref({ ...emptyQR });
const selectedQR = ref(null);

let nextId = 5;

const filteredQRCodes = computed(() => {
    if (!filterText.value.trim()) return qrCodes.value;
    const q = filterText.value.toLowerCase();
    return qrCodes.value.filter((item) => {
        return item.name.toLowerCase().includes(q) || item.location.toLowerCase().includes(q) || item.companyName.toLowerCase().includes(q) || item.branchName.toLowerCase().includes(q);
    });
});

const openNew = () => {
    qr.value = { ...emptyQR };
    isEditing.value = false;
    submitted.value = false;
    qrDialog.value = true;
};

const editQR = (data) => {
    qr.value = { ...data };
    isEditing.value = true;
    submitted.value = false;
    qrDialog.value = true;
};

const confirmDelete = (data) => {
    selectedQR.value = data;
    deleteDialog.value = true;
};

const saveQR = () => {
    submitted.value = true;

    if (!qr.value.name.trim() || !qr.value.location.trim() || !qr.value.companyId || !qr.value.branchId) return;

    const comp = companies.value.find((c) => c.id === qr.value.companyId);
    const br = branches.value.find((b) => b.id === qr.value.branchId);
    qr.value.companyName = comp ? comp.name : '';
    qr.value.branchName = br ? br.name : '';

    if (isEditing.value) {
        const idx = qrCodes.value.findIndex((q) => q.id === qr.value.id);
        if (idx !== -1) qrCodes.value[idx] = { ...qr.value };
        toast.add({ severity: 'success', summary: 'Updated', detail: 'QR Code updated successfully.', life: 3000 });
    } else {
        qr.value.id = nextId++;
        qr.value.createdAt = new Date().toISOString().replace('T', ' ').slice(0, 19);
        qrCodes.value.push({ ...qr.value });
        toast.add({ severity: 'success', summary: 'Created', detail: 'QR Code created successfully.', life: 3000 });
    }
    qrDialog.value = false;
};

const deleteQRConfirmed = () => {
    qrCodes.value = qrCodes.value.filter((q) => q.id !== selectedQR.value.id);
    deleteDialog.value = false;
    selectedQR.value = null;
    toast.add({ severity: 'success', summary: 'Deleted', detail: 'QR Code deleted.', life: 3000 });
};

const getStatusSeverity = (status) => {
    return status === 'Active' ? 'success' : 'secondary';
};
</script>

<template>
    <Toast />
    <div class="card">
        <div class="font-semibold text-xl mb-4">QR Code Management</div>

        <!-- Filter Bar -->
        <div class="mb-4">
            <IconField>
                <InputIcon class="pi pi-search" />
                <InputText v-model="filterText" placeholder="Search by name, location, branch..." class="w-full" />
            </IconField>
        </div>

        <DataTable :value="filteredQRCodes" :paginator="true" :rows="10" dataKey="id" :rowHover="true" responsiveLayout="scroll">
            <template #header>
                <div class="flex justify-between items-center">
                    <span class="text-xl text-surface-900 dark:text-surface-0 font-bold">QR Codes</span>
                    <Button label="Create QR Code" icon="pi pi-plus" size="small" @click="openNew" />
                </div>
            </template>
            <template #empty> No QR codes found. </template>
            <Column field="name" header="Name" sortable style="min-width: 14rem"></Column>
            <Column field="location" header="Location" sortable style="min-width: 16rem"></Column>
            <Column field="companyName" header="Company" sortable style="min-width: 12rem"></Column>
            <Column field="branchName" header="Branch" sortable style="min-width: 12rem"></Column>
            <Column field="status" header="Status" sortable style="min-width: 8rem">
                <template #body="{ data }">
                    <Tag :value="data.status" :severity="getStatusSeverity(data.status)" />
                </template>
            </Column>
            <Column field="createdAt" header="Created" sortable style="min-width: 12rem"></Column>
            <Column header="QR" style="min-width: 6rem">
                <template #body>
                    <div class="w-10 h-10 bg-surface-200 dark:bg-surface-700 rounded flex items-center justify-center">
                        <i class="pi pi-qrcode text-xl text-surface-500"></i>
                    </div>
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

    <!-- QR Code Dialog -->
    <Dialog v-model:visible="qrDialog" :header="isEditing ? 'Edit QR Code' : 'Create QR Code'" :modal="true" :style="{ width: '550px' }">
        <form @submit.prevent="saveQR">
            <div class="flex flex-col gap-6 mt-4">
                <div class="flex flex-col gap-2">
                    <label class="font-medium">Name *</label>
                    <InputText v-model="qr.name" :invalid="submitted && !qr.name.trim()" placeholder="e.g. Main Entrance, Server Room" />
                    <small v-if="submitted && !qr.name.trim()" class="text-red-500">Name is required.</small>
                </div>

                <div class="flex flex-col gap-2">
                    <label class="font-medium">Location *</label>
                    <InputText v-model="qr.location" :invalid="submitted && !qr.location.trim()" placeholder="e.g. Building A — Front Door" />
                    <small v-if="submitted && !qr.location.trim()" class="text-red-500">Location is required.</small>
                </div>

                <div class="flex flex-col gap-2">
                    <label class="font-medium">Company *</label>
                    <Select v-model="qr.companyId" :options="companies" optionLabel="name" optionValue="id" placeholder="Select a company" :invalid="submitted && !qr.companyId" @change="onCompanyChange" />
                    <small v-if="submitted && !qr.companyId" class="text-red-500">Company is required.</small>
                </div>

                <div class="flex flex-col gap-2">
                    <label class="font-medium">Branch *</label>
                    <Select v-model="qr.branchId" :options="filteredBranchOptions" optionLabel="name" optionValue="id" placeholder="Select a branch" :invalid="submitted && !qr.branchId" :disabled="!qr.companyId" />
                    <small v-if="submitted && !qr.branchId" class="text-red-500">Branch is required.</small>
                </div>

                <div class="flex flex-col gap-2">
                    <label class="font-medium">Status</label>
                    <Select v-model="qr.status" :options="['Active', 'Inactive']" placeholder="Select status" />
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
            <span>Are you sure you want to delete <strong>{{ selectedQR?.name }}</strong>?</span>
        </div>
        <template #footer>
            <div class="flex justify-end gap-2">
                <Button label="No" icon="pi pi-times" severity="secondary" @click="deleteDialog = false" />
                <Button label="Yes" icon="pi pi-check" severity="danger" @click="deleteQRConfirmed" />
            </div>
        </template>
    </Dialog>
</template>
