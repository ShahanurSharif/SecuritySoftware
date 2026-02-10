<script setup>
import { ref, computed } from 'vue';
import { useToast } from 'primevue/usetoast';

const toast = useToast();

const companies = ref([
    {
        id: 1,
        name: 'SecureCorp Ltd.',
        email: 'info@securecorp.com',
        address: { full: '123 Main St, New York, NY 10001', flat: '123', street: 'Main St', suburb: 'Manhattan', postalCode: '10001', state: 'NY', country: 'US' },
        phones: [
            { id: 1, number: '+1-212-555-0100', label: 'Main Office' },
            { id: 2, number: '+1-212-555-0101', label: 'Reception' }
        ],
        description: 'Headquarters company for security operations'
    },
    {
        id: 2,
        name: 'CyberShield Inc.',
        email: 'contact@cybershield.com',
        address: { full: '456 Market Ave, San Francisco, CA 94102', flat: '456', street: 'Market Ave', suburb: 'SoMa', postalCode: '94102', state: 'CA', country: 'US' },
        phones: [{ id: 1, number: '+1-415-555-0200', label: 'Head Office' }],
        description: 'West coast security division'
    }
]);

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

let nextId = 3;
let nextPhoneId = 10;

const isValidPhone = (val) => /^[+]?[\d\s()-]{7,20}$/.test(val);
const isValidEmail = (val) => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(val);

// --- Filter ---
const filteredCompanies = computed(() => {
    if (!filterText.value.trim()) return companies.value;
    const q = filterText.value.toLowerCase();
    return companies.value.filter((c) => {
        const addrStr = [c.address.full, c.address.flat, c.address.street, c.address.suburb, c.address.postalCode, c.address.state, c.address.country].filter(Boolean).join(' ').toLowerCase();
        const phoneStr = c.phones.map((p) => p.number).join(' ').toLowerCase();
        return c.name.toLowerCase().includes(q) || addrStr.includes(q) || phoneStr.includes(q);
    });
});

// --- Google Places autocomplete stub ---
const addressSuggestions = ref([]);
const searchingAddress = ref(false);

const searchAddress = (event) => {
    const query = event.query;
    searchingAddress.value = true;
    // TODO: Replace with real Google Places API call
    setTimeout(() => {
        addressSuggestions.value = [
            { full: `${query}, Suburb, State 00000, Country`, flat: '', street: query, suburb: 'Suburb', postalCode: '00000', state: 'State', country: 'Country' }
        ];
        searchingAddress.value = false;
    }, 300);
};

const onAddressSelect = (event) => {
    const selected = event.value;
    if (selected && typeof selected === 'object') {
        company.value.address = { ...selected };
    }
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

const saveCompany = () => {
    submitted.value = true;

    if (!company.value.name.trim()) return;
    if (!company.value.email.trim() || !isValidEmail(company.value.email)) return;
    if (!company.value.address.street.trim()) return;

    if (isEditing.value) {
        const idx = companies.value.findIndex((c) => c.id === company.value.id);
        if (idx !== -1) companies.value[idx] = { ...company.value, address: { ...company.value.address }, phones: company.value.phones.map((p) => ({ ...p })) };
        toast.add({ severity: 'success', summary: 'Updated', detail: 'Company updated successfully.', life: 3000 });
    } else {
        company.value.id = nextId++;
        companies.value.push({ ...company.value, address: { ...company.value.address }, phones: company.value.phones.map((p) => ({ ...p })) });
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
        phone.value.id = nextPhoneId++;
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
                <InputText v-model="filterText" placeholder="Search by name, address, phone number..." class="w-full" />
            </IconField>
        </div>

        <DataTable :value="filteredCompanies" :paginator="true" :rows="10" dataKey="id" :rowHover="true" responsiveLayout="scroll">
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

                <!-- Google Address Section -->
                <div class="flex flex-col gap-4">
                    <label class="font-medium">Head Office Address *</label>
                    <AutoComplete v-model="company.address.full" :suggestions="addressSuggestions" optionLabel="full" placeholder="Search address from Google..." @complete="searchAddress" @item-select="onAddressSelect" forceSelection:false class="w-full" />
                    <small class="text-muted-color -mt-2"><i class="pi pi-map-marker mr-1"></i>Select from Google Places or fill manually below</small>

                    <div class="grid grid-cols-2 gap-4">
                        <div class="flex flex-col gap-2">
                            <label class="text-sm">Flat / House No.</label>
                            <InputText v-model="company.address.flat" placeholder="Flat / House No." />
                        </div>
                        <div class="flex flex-col gap-2">
                            <label class="text-sm">Street *</label>
                            <InputText v-model="company.address.street" :invalid="submitted && !company.address.street.trim()" placeholder="Street" />
                            <small v-if="submitted && !company.address.street.trim()" class="text-red-500">Street is required.</small>
                        </div>
                    </div>
                    <div class="grid grid-cols-2 gap-4">
                        <div class="flex flex-col gap-2">
                            <label class="text-sm">Suburb</label>
                            <InputText v-model="company.address.suburb" placeholder="Suburb" />
                        </div>
                        <div class="flex flex-col gap-2">
                            <label class="text-sm">Postal Code</label>
                            <InputText v-model="company.address.postalCode" placeholder="Postal Code" />
                        </div>
                    </div>
                    <div class="grid grid-cols-2 gap-4">
                        <div class="flex flex-col gap-2">
                            <label class="text-sm">State</label>
                            <InputText v-model="company.address.state" placeholder="State" />
                        </div>
                        <div class="flex flex-col gap-2">
                            <label class="text-sm">Country</label>
                            <InputText v-model="company.address.country" placeholder="Country" />
                        </div>
                    </div>
                </div>

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
