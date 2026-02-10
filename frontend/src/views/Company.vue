<script setup>
import { ref } from 'vue';
import { useToast } from 'primevue/usetoast';

const toast = useToast();

const companies = ref([
    { id: 1, name: 'SecureCorp Ltd.', address: '123 Main St, New York, NY 10001', phone: '+1-212-555-0100', description: 'Headquarters company for security operations' },
    { id: 2, name: 'CyberShield Inc.', address: '456 Market Ave, San Francisco, CA 94102', phone: '+1-415-555-0200', description: 'West coast security division' }
]);

const companyDialog = ref(false);
const deleteDialog = ref(false);
const isEditing = ref(false);
const submitted = ref(false);

const emptyCompany = { id: null, name: '', address: '', phone: '', description: '' };
const company = ref({ ...emptyCompany });
const selectedCompany = ref(null);

let nextId = 3;

const isValidPhone = (val) => /^[+]?[\d\s()-]{7,20}$/.test(val);

const openNew = () => {
    company.value = { ...emptyCompany };
    isEditing.value = false;
    submitted.value = false;
    companyDialog.value = true;
};

const editCompany = (data) => {
    company.value = { ...data };
    isEditing.value = true;
    submitted.value = false;
    companyDialog.value = true;
};

const confirmDelete = (data) => {
    selectedCompany.value = data;
    deleteDialog.value = true;
};

const saveCompany = () => {
    submitted.value = true;

    if (!company.value.name.trim() || !company.value.address.trim() || !company.value.phone.trim()) return;
    if (!isValidPhone(company.value.phone)) return;

    if (isEditing.value) {
        const idx = companies.value.findIndex((c) => c.id === company.value.id);
        if (idx !== -1) companies.value[idx] = { ...company.value };
        toast.add({ severity: 'success', summary: 'Updated', detail: 'Company updated successfully.', life: 3000 });
    } else {
        company.value.id = nextId++;
        companies.value.push({ ...company.value });
        toast.add({ severity: 'success', summary: 'Created', detail: 'Company created successfully.', life: 3000 });
    }
    companyDialog.value = false;
};

const deleteCompanyConfirmed = () => {
    companies.value = companies.value.filter((c) => c.id !== selectedCompany.value.id);
    deleteDialog.value = false;
    selectedCompany.value = null;
    toast.add({ severity: 'success', summary: 'Deleted', detail: 'Company deleted.', life: 3000 });
};
</script>

<template>
    <Toast />
    <div class="card">
        <div class="font-semibold text-xl mb-4">Company Management</div>
        <DataTable :value="companies" :paginator="true" :rows="10" dataKey="id" :rowHover="true" responsiveLayout="scroll">
            <template #header>
                <div class="flex justify-between items-center">
                    <span class="text-xl text-surface-900 dark:text-surface-0 font-bold">Companies</span>
                    <Button label="Add Company" icon="pi pi-plus" size="small" @click="openNew" />
                </div>
            </template>
            <template #empty> No companies found. </template>
            <Column field="name" header="Name" sortable style="min-width: 14rem"></Column>
            <Column field="address" header="Head Office Address" sortable style="min-width: 18rem"></Column>
            <Column field="phone" header="Phone" sortable style="min-width: 12rem"></Column>
            <Column field="description" header="Description" style="min-width: 16rem">
                <template #body="{ data }">
                    <span class="line-clamp-2">{{ data.description }}</span>
                </template>
            </Column>
            <Column header="Actions" style="min-width: 10rem">
                <template #body="{ data }">
                    <div class="flex gap-2">
                        <Button icon="pi pi-pencil" rounded outlined severity="info" size="small" @click="editCompany(data)" />
                        <Button icon="pi pi-trash" rounded outlined severity="danger" size="small" @click="confirmDelete(data)" />
                    </div>
                </template>
            </Column>
        </DataTable>
    </div>

    <!-- Company Dialog -->
    <Dialog v-model:visible="companyDialog" :header="isEditing ? 'Edit Company' : 'Add Company'" :modal="true" :style="{ width: '550px' }">
        <form @submit.prevent="saveCompany">
            <div class="flex flex-col gap-6 mt-4">
                <div class="flex flex-col gap-2">
                    <label for="companyName" class="font-medium">Company Name *</label>
                    <InputText id="companyName" v-model="company.name" :invalid="submitted && !company.name.trim()" placeholder="Enter company name" />
                    <small v-if="submitted && !company.name.trim()" class="text-red-500">Company name is required.</small>
                </div>

                <div class="flex flex-col gap-2">
                    <label for="companyAddress" class="font-medium">Head Office Address *</label>
                    <Textarea id="companyAddress" v-model="company.address" rows="3" :invalid="submitted && !company.address.trim()" placeholder="Enter head office address" />
                    <small v-if="submitted && !company.address.trim()" class="text-red-500">Address is required.</small>
                </div>

                <div class="flex flex-col gap-2">
                    <label for="companyPhone" class="font-medium">Phone Number *</label>
                    <InputText id="companyPhone" v-model="company.phone" :invalid="submitted && (!company.phone.trim() || !isValidPhone(company.phone))" placeholder="+1-212-555-0100" />
                    <small v-if="submitted && !company.phone.trim()" class="text-red-500">Phone number is required.</small>
                    <small v-else-if="submitted && !isValidPhone(company.phone)" class="text-red-500">Enter a valid phone number.</small>
                </div>

                <div class="flex flex-col gap-2">
                    <label for="companyDesc" class="font-medium">Description</label>
                    <Textarea id="companyDesc" v-model="company.description" rows="3" placeholder="Company description (optional)" />
                </div>
            </div>

            <div class="flex justify-end gap-2 mt-6">
                <Button label="Cancel" icon="pi pi-times" severity="secondary" @click="companyDialog = false" type="button" />
                <Button type="submit" :label="isEditing ? 'Update' : 'Save'" icon="pi pi-check" />
            </div>
        </form>
    </Dialog>

    <!-- Delete Confirmation -->
    <Dialog v-model:visible="deleteDialog" header="Confirm Delete" :modal="true" :style="{ width: '400px' }">
        <div class="flex items-center gap-4">
            <i class="pi pi-exclamation-triangle text-3xl text-red-500" />
            <span>Are you sure you want to delete <strong>{{ selectedCompany?.name }}</strong>?</span>
        </div>
        <template #footer>
            <div class="flex justify-end gap-2">
                <Button label="No" icon="pi pi-times" severity="secondary" @click="deleteDialog = false" />
                <Button label="Yes" icon="pi pi-check" severity="danger" @click="deleteCompanyConfirmed" />
            </div>
        </template>
    </Dialog>
</template>
