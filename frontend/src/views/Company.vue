<script setup>
import { ref, onMounted } from 'vue';
import { useToast } from 'primevue/usetoast';
import api from '@/services/api';
import AddressField from '@/components/AddressField.vue';

const toast = useToast();
const loading = ref(false);

const companies = ref([]);
const totalRecords = ref(0);
const currentPage = ref(1);
const rowsPerPage = ref(10);
const sortField = ref('name');
const sortOrder = ref(1);

const companyDialog = ref(false);
const deleteDialog = ref(false);
const phoneDialog = ref(false);
const deletePhoneDialog = ref(false);
const isEditing = ref(false);
const submitted = ref(false);
const phoneSubmitted = ref(false);

const filterText = ref('');

const emptyAddress = { full: '', flat: '', street: '', suburb: '', postalCode: '', state: '', country: '' };
const emptyCompany = { id: null, name: '', email: '', address: { ...emptyAddress }, phones: [], description: '' };
const company = ref({ ...emptyCompany, address: { ...emptyAddress }, phones: [] });
const selectedCompany = ref(null);

const emptyPhone = { id: null, number: '', label: '' };
const phone = ref({ ...emptyPhone });
const selectedPhone = ref(null);
const isEditingPhone = ref(false);

const isValidPhone = (val) => /^[+]?[\d\s()-]{7,20}$/.test(val);
const isValidEmail = (val) => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(val);

// --- Helpers: map between API snake_case ↔ frontend camelCase ---
const mapFromApi = (c) => ({
    id: c.id,
    name: c.name,
    email: c.email,
    description: c.description || '',
    address: {
        full: [c.address.flat, c.address.street, c.address.suburb, c.address.state, c.address.postal_code, c.address.country].filter(Boolean).join(', '),
        flat: c.address.flat || '',
        street: c.address.street || '',
        suburb: c.address.suburb || '',
        postalCode: c.address.postal_code || '',
        state: c.address.state || '',
        country: c.address.country || ''
    },
    phones: (c.phones || []).map((p) => ({ id: p.id, number: p.number, label: p.label || '' }))
});

const mapToApi = (c) => ({
    name: c.name,
    email: c.email,
    description: c.description,
    address: {
        flat: c.address.flat,
        street: c.address.street,
        suburb: c.address.suburb,
        postal_code: c.address.postalCode,
        state: c.address.state,
        country: c.address.country
    },
    phones: c.phones.map((p) => ({ number: p.number, label: p.label }))
});

// --- Fetch companies from API (server-side pagination, search, ordering) ---
const fetchCompanies = async () => {
    loading.value = true;
    try {
        const params = {
            page: currentPage.value,
            page_size: rowsPerPage.value
        };
        if (filterText.value.trim()) params.search = filterText.value.trim();
        if (sortField.value) {
            const fieldMap = { name: 'name', email: 'email' };
            const apiField = fieldMap[sortField.value] || sortField.value;
            params.ordering = sortOrder.value === 1 ? apiField : `-${apiField}`;
        }
        const { data } = await api.get('/companies/', { params });
        companies.value = (data.results || []).map(mapFromApi);
        totalRecords.value = data.count || 0;
    } catch {
        toast.add({ severity: 'error', summary: 'Error', detail: 'Failed to load companies.', life: 4000 });
    } finally {
        loading.value = false;
    }
};

onMounted(fetchCompanies);

// --- Server-side event handlers ---
const onPage = (event) => {
    currentPage.value = event.page + 1;
    rowsPerPage.value = event.rows;
    fetchCompanies();
};

const onSort = (event) => {
    sortField.value = event.sortField;
    sortOrder.value = event.sortOrder;
    currentPage.value = 1;
    fetchCompanies();
};

let searchTimeout = null;
const onSearch = () => {
    clearTimeout(searchTimeout);
    searchTimeout = setTimeout(() => {
        currentPage.value = 1;
        fetchCompanies();
    }, 400);
};

// --- Company CRUD ---
const openNew = () => {
    company.value = { ...emptyCompany, address: { ...emptyAddress }, phones: [] };
    isEditing.value = false;
    submitted.value = false;
    companyDialog.value = true;
};

const editCompany = (data) => {
    company.value = { ...data, address: { ...data.address }, phones: data.phones.map((p) => ({ ...p })) };
    isEditing.value = true;
    submitted.value = false;
    companyDialog.value = true;
};

const confirmDelete = (data) => {
    selectedCompany.value = data;
    deleteDialog.value = true;
};

const saveCompany = async () => {
    submitted.value = true;

    if (!company.value.name.trim()) return;
    if (!company.value.email.trim() || !isValidEmail(company.value.email)) return;
    if (!company.value.address.street.trim()) return;

    const payload = mapToApi(company.value);

    try {
        if (isEditing.value) {
            await api.put(`/companies/${company.value.id}/`, payload);
            toast.add({ severity: 'success', summary: 'Updated', detail: 'Company updated successfully.', life: 3000 });
        } else {
            await api.post('/companies/', payload);
            toast.add({ severity: 'success', summary: 'Created', detail: 'Company created successfully.', life: 3000 });
        }
        companyDialog.value = false;
        await fetchCompanies();
    } catch (err) {
        const detail = err.response?.data?.name?.[0] || err.response?.data?.detail || 'Failed to save company.';
        toast.add({ severity: 'error', summary: 'Error', detail, life: 4000 });
    }
};

const deleteCompanyConfirmed = async () => {
    try {
        await api.delete(`/companies/${selectedCompany.value.id}/`);
        deleteDialog.value = false;
        selectedCompany.value = null;
        toast.add({ severity: 'success', summary: 'Deleted', detail: 'Company deleted.', life: 3000 });
        await fetchCompanies();
    } catch {
        toast.add({ severity: 'error', summary: 'Error', detail: 'Failed to delete company.', life: 4000 });
    }
};

// --- Phone CRUD ---
const addPhone = () => {
    phone.value = { ...emptyPhone };
    isEditingPhone.value = false;
    phoneSubmitted.value = false;
    phoneDialog.value = true;
};

const editPhone = (p) => {
    phone.value = { ...p };
    isEditingPhone.value = true;
    phoneSubmitted.value = false;
    phoneDialog.value = true;
};

const confirmDeletePhone = (p) => {
    selectedPhone.value = p;
    deletePhoneDialog.value = true;
};

const savePhone = () => {
    phoneSubmitted.value = true;

    if (!phone.value.number.trim() || !isValidPhone(phone.value.number)) return;

    if (isEditingPhone.value) {
        const idx = company.value.phones.findIndex((p) => p.id === phone.value.id);
        if (idx !== -1) company.value.phones[idx] = { ...phone.value };
        toast.add({ severity: 'success', summary: 'Updated', detail: 'Phone updated.', life: 3000 });
    } else {
        phone.value.id = Date.now();
        company.value.phones.push({ ...phone.value });
        toast.add({ severity: 'success', summary: 'Added', detail: 'Phone added.', life: 3000 });
    }
    phoneDialog.value = false;
};

const deletePhoneConfirmed = () => {
    company.value.phones = company.value.phones.filter((p) => p.id !== selectedPhone.value.id);
    deletePhoneDialog.value = false;
    selectedPhone.value = null;
    toast.add({ severity: 'success', summary: 'Deleted', detail: 'Phone removed.', life: 3000 });
};

const formatAddress = (addr) => {
    if (!addr) return '';
    return [addr.flat, addr.street, addr.suburb, addr.state, addr.postalCode, addr.country].filter(Boolean).join(', ');
};
</script>

<template>
    <Toast />
    <div class="card">
        <div class="font-semibold text-xl mb-4">Company Management</div>

        <!-- Filter Bar -->
        <div class="mb-4">
            <IconField>
                <InputIcon class="pi pi-search" />
                <InputText v-model="filterText" placeholder="Search by name, address, phone number..." class="w-full" @input="onSearch" />
            </IconField>
        </div>

        <DataTable :value="companies" :paginator="true" :rows="rowsPerPage" :totalRecords="totalRecords" :lazy="true" :loading="loading" :rowHover="true" :rowsPerPageOptions="[10, 25, 50]" dataKey="id" responsiveLayout="scroll" @page="onPage" @sort="onSort" :sortField="sortField" :sortOrder="sortOrder">
            <template #header>
                <div class="flex justify-between items-center">
                    <span class="text-xl text-surface-900 dark:text-surface-0 font-bold">Companies</span>
                    <Button label="Add Company" icon="pi pi-plus" size="small" @click="openNew" />
                </div>
            </template>
            <template #empty> No companies found. </template>
            <Column field="name" header="Name" sortable style="min-width: 14rem"></Column>
            <Column field="email" header="Email" sortable style="min-width: 14rem"></Column>
            <Column header="Address" sortable style="min-width: 18rem">
                <template #body="{ data }">{{ formatAddress(data.address) }}</template>
            </Column>
            <Column header="Phone(s)" style="min-width: 14rem">
                <template #body="{ data }">
                    <div class="flex flex-col gap-1">
                        <span v-for="p in data.phones" :key="p.id" class="text-sm">
                            {{ p.number }}<span v-if="p.label" class="text-muted-color ml-1">({{ p.label }})</span>
                        </span>
                        <span v-if="!data.phones.length" class="text-muted-color text-sm">—</span>
                    </div>
                </template>
            </Column>
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
    <Dialog v-model:visible="companyDialog" :header="isEditing ? 'Edit Company' : 'Add Company'" :modal="true" :style="{ width: '700px' }">
        <form @submit.prevent="saveCompany">
            <div class="flex flex-col gap-6 mt-4">
                <div class="flex flex-col gap-2">
                    <label class="font-medium">Company Name *</label>
                    <InputText v-model="company.name" :invalid="submitted && !company.name.trim()" placeholder="Enter company name" />
                    <small v-if="submitted && !company.name.trim()" class="text-red-500">Company name is required.</small>
                </div>

                <div class="flex flex-col gap-2">
                    <label class="font-medium">Email *</label>
                    <InputText v-model="company.email" type="email" :invalid="submitted && (!company.email.trim() || !isValidEmail(company.email))" placeholder="company@example.com" />
                    <small v-if="submitted && !company.email.trim()" class="text-red-500">Email is required.</small>
                    <small v-else-if="submitted && !isValidEmail(company.email)" class="text-red-500">Enter a valid email address.</small>
                </div>

                <AddressField v-model="company.address" :submitted="submitted" label="Address *" />

                <!-- Phone Numbers CRUD -->
                <div class="flex flex-col gap-2">
                    <div class="flex justify-between items-center">
                        <label class="font-medium">Phone Numbers</label>
                        <Button label="Add Phone" icon="pi pi-plus" size="small" text @click="addPhone" type="button" />
                    </div>
                    <DataTable :value="company.phones" dataKey="id" size="small" :rowHover="true">
                        <template #empty><span class="text-muted-color text-sm">No phone numbers added yet.</span></template>
                        <Column field="number" header="Number" style="min-width: 12rem"></Column>
                        <Column field="label" header="Label" style="min-width: 10rem">
                            <template #body="{ data }">{{ data.label || '—' }}</template>
                        </Column>
                        <Column header="Actions" style="min-width: 8rem">
                            <template #body="{ data }">
                                <div class="flex gap-2">
                                    <Button icon="pi pi-pencil" rounded outlined severity="info" size="small" @click="editPhone(data)" type="button" />
                                    <Button icon="pi pi-trash" rounded outlined severity="danger" size="small" @click="confirmDeletePhone(data)" type="button" />
                                </div>
                            </template>
                        </Column>
                    </DataTable>
                </div>

                <div class="flex flex-col gap-2">
                    <label class="font-medium">Description</label>
                    <Textarea v-model="company.description" rows="3" placeholder="Company description (optional)" />
                </div>
            </div>

            <div class="flex justify-end gap-2 mt-6">
                <Button label="Cancel" icon="pi pi-times" severity="secondary" @click="companyDialog = false" type="button" />
                <Button type="submit" :label="isEditing ? 'Update' : 'Save'" icon="pi pi-check" />
            </div>
        </form>
    </Dialog>

    <!-- Phone Add/Edit Dialog -->
    <Dialog v-model:visible="phoneDialog" :header="isEditingPhone ? 'Edit Phone' : 'Add Phone'" :modal="true" :style="{ width: '400px' }">
        <form @submit.prevent="savePhone">
            <div class="flex flex-col gap-6 mt-4">
                <div class="flex flex-col gap-2">
                    <label class="font-medium">Phone Number *</label>
                    <InputText v-model="phone.number" :invalid="phoneSubmitted && (!phone.number.trim() || !isValidPhone(phone.number))" placeholder="+1-212-555-0100" />
                    <small v-if="phoneSubmitted && !phone.number.trim()" class="text-red-500">Phone number is required.</small>
                    <small v-else-if="phoneSubmitted && !isValidPhone(phone.number)" class="text-red-500">Enter a valid phone number.</small>
                </div>

                <div class="flex flex-col gap-2">
                    <label class="font-medium">Label</label>
                    <InputText v-model="phone.label" placeholder="e.g. Main Office, Reception" />
                </div>
            </div>

            <div class="flex justify-end gap-2 mt-6">
                <Button label="Cancel" icon="pi pi-times" severity="secondary" @click="phoneDialog = false" type="button" />
                <Button type="submit" :label="isEditingPhone ? 'Update' : 'Add'" icon="pi pi-check" />
            </div>
        </form>
    </Dialog>

    <!-- Delete Company Confirmation -->
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

    <!-- Delete Phone Confirmation -->
    <Dialog v-model:visible="deletePhoneDialog" header="Confirm Delete" :modal="true" :style="{ width: '400px' }">
        <div class="flex items-center gap-4">
            <i class="pi pi-exclamation-triangle text-3xl text-red-500" />
            <span>Remove phone <strong>{{ selectedPhone?.number }}</strong>?</span>
        </div>
        <template #footer>
            <div class="flex justify-end gap-2">
                <Button label="No" icon="pi pi-times" severity="secondary" @click="deletePhoneDialog = false" />
                <Button label="Yes" icon="pi pi-check" severity="danger" @click="deletePhoneConfirmed" />
            </div>
        </template>
    </Dialog>
</template>
