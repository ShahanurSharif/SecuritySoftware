<script setup>
import { ref, computed, onMounted } from 'vue';
import { useToast } from 'primevue/usetoast';
import api from '@/services/api';
import { useGooglePlaces } from '@/composables/useGooglePlaces';

const toast = useToast();
const loading = ref(false);

const companies = ref([]);
const branches = ref([]);
const totalRecords = ref(0);
const currentPage = ref(1);
const rowsPerPage = ref(10);
const sortField = ref('name');
const sortOrder = ref(1);

const branchDialog = ref(false);
const deleteDialog = ref(false);
const staffDialog = ref(false);
const deleteStaffDialog = ref(false);
const isEditing = ref(false);
const submitted = ref(false);
const staffSubmitted = ref(false);

// --- Filter refs ---
const filterCompany = ref(null);
const filterBranchName = ref('');
const filterPhone = ref('');
const filterAddress = ref('');
const filterState = ref('');
const filterSuburb = ref('');

const emptyAddress = { full: '', flat: '', street: '', suburb: '', postalCode: '', state: '', country: '' };
const emptyBranch = { id: null, companyId: null, companyName: '', name: '', address: { ...emptyAddress }, managerNumber: '', storeNumber: '', staff: [] };
const emptyStaff = { id: null, name: '', designation: '', number: '', email: '' };
const branch = ref({ ...emptyBranch, address: { ...emptyAddress }, staff: [] });
const selectedBranch = ref(null);
const staffMember = ref({ ...emptyStaff });
const selectedStaff = ref(null);
const isEditingStaff = ref(false);

const showStaffPanel = ref(false);
const viewStaffBranchId = ref(null);
const viewStaffBranch = computed(() => branches.value.find((b) => b.id === viewStaffBranchId.value));

const isValidPhone = (val) => /^[+]?[\d\s()-]{7,20}$/.test(val);
const isValidEmail = (val) => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(val);

// --- Helpers: map API ↔ frontend ---
const mapFromApi = (b) => ({
    id: b.id,
    companyId: b.company,
    companyName: b.company_name || '',
    name: b.name,
    address: {
        full: [b.address.flat, b.address.street, b.address.suburb, b.address.state, b.address.postal_code, b.address.country].filter(Boolean).join(', '),
        flat: b.address.flat || '',
        street: b.address.street || '',
        suburb: b.address.suburb || '',
        postalCode: b.address.postal_code || '',
        state: b.address.state || '',
        country: b.address.country || ''
    },
    managerNumber: b.front_desk_number || '',
    storeNumber: b.store_number || '',
    staff: (b.staff || []).map((s) => ({ id: s.id, name: s.name, designation: s.designation, number: s.phone, email: s.email || '' }))
});

const mapToApi = (b) => ({
    company: b.companyId,
    name: b.name,
    address: {
        flat: b.address.flat,
        street: b.address.street,
        suburb: b.address.suburb,
        postal_code: b.address.postalCode,
        state: b.address.state,
        country: b.address.country
    },
    front_desk_number: b.managerNumber,
    store_number: b.storeNumber,
    staff: b.staff.map((s) => ({ name: s.name, designation: s.designation, phone: s.number, email: s.email }))
});

// --- Fetch ---
const fetchCompanies = async () => {
    try {
        const { data } = await api.get('/companies/lite/');
        companies.value = data;
    } catch {
        toast.add({ severity: 'error', summary: 'Error', detail: 'Failed to load companies.', life: 4000 });
    }
};

const fetchBranches = async () => {
    loading.value = true;
    try {
        const params = {
            page: currentPage.value,
            page_size: rowsPerPage.value
        };
        // Filters
        if (filterCompany.value) params.company = filterCompany.value;
        // Build search string from remaining text filters
        const searchParts = [filterBranchName.value, filterPhone.value, filterAddress.value, filterState.value, filterSuburb.value].filter((v) => v.trim());
        if (searchParts.length) params.search = searchParts.join(' ');
        // Sorting
        if (sortField.value) {
            const fieldMap = { name: 'name', companyName: 'company__name', managerNumber: 'front_desk_number', storeNumber: 'store_number' };
            const apiField = fieldMap[sortField.value] || sortField.value;
            params.ordering = sortOrder.value === 1 ? apiField : `-${apiField}`;
        }
        const { data } = await api.get('/branches/', { params });
        branches.value = (data.results || []).map(mapFromApi);
        totalRecords.value = data.count || 0;
    } catch {
        toast.add({ severity: 'error', summary: 'Error', detail: 'Failed to load branches.', life: 4000 });
    } finally {
        loading.value = false;
    }
};

onMounted(async () => {
    await Promise.all([fetchCompanies(), fetchBranches()]);
});

// --- Server-side event handlers ---
const onPage = (event) => {
    currentPage.value = event.page + 1;
    rowsPerPage.value = event.rows;
    fetchBranches();
};

const onSort = (event) => {
    sortField.value = event.sortField;
    sortOrder.value = event.sortOrder;
    currentPage.value = 1;
    fetchBranches();
};

let searchTimeout = null;
const onFilterChange = () => {
    clearTimeout(searchTimeout);
    searchTimeout = setTimeout(() => {
        currentPage.value = 1;
        fetchBranches();
    }, 400);
};

const clearFilters = () => {
    filterCompany.value = null;
    filterBranchName.value = '';
    filterPhone.value = '';
    filterAddress.value = '';
    filterState.value = '';
    filterSuburb.value = '';
    currentPage.value = 1;
    fetchBranches();
};

// --- Google Places Autocomplete ---
const { suggestions: addressSuggestions, search: searchPlaces, getPlaceDetails } = useGooglePlaces();

const searchAddress = (event) => {
    searchPlaces(event.query);
};

const onAddressSelect = async (event) => {
    const selected = event.value;
    if (selected && selected.placeId) {
        const details = await getPlaceDetails(selected.placeId);
        if (details) {
            branch.value.address = { ...details };
        }
    }
};

// --- Branch CRUD ---
const openNew = () => {
    branch.value = { ...emptyBranch, address: { ...emptyAddress }, staff: [] };
    isEditing.value = false;
    submitted.value = false;
    branchDialog.value = true;
};

const editBranch = (data) => {
    branch.value = { ...data, address: { ...data.address }, staff: data.staff.map((s) => ({ ...s })) };
    isEditing.value = true;
    submitted.value = false;
    branchDialog.value = true;
};

const confirmDelete = (data) => {
    selectedBranch.value = data;
    deleteDialog.value = true;
};

const saveBranch = async () => {
    submitted.value = true;

    if (!branch.value.companyId || !branch.value.name.trim() || !branch.value.address.street.trim() || !branch.value.managerNumber.trim() || !branch.value.storeNumber.trim()) return;
    if (!isValidPhone(branch.value.managerNumber)) return;

    const payload = mapToApi(branch.value);

    try {
        if (isEditing.value) {
            await api.put(`/branches/${branch.value.id}/`, payload);
            toast.add({ severity: 'success', summary: 'Updated', detail: 'Branch updated successfully.', life: 3000 });
        } else {
            await api.post('/branches/', payload);
            toast.add({ severity: 'success', summary: 'Created', detail: 'Branch created successfully.', life: 3000 });
        }
        branchDialog.value = false;
        await fetchBranches();
    } catch (err) {
        const detail = err.response?.data?.name?.[0] || err.response?.data?.detail || 'Failed to save branch.';
        toast.add({ severity: 'error', summary: 'Error', detail, life: 4000 });
    }
};

const deleteBranchConfirmed = async () => {
    try {
        await api.delete(`/branches/${selectedBranch.value.id}/`);
        deleteDialog.value = false;
        selectedBranch.value = null;
        toast.add({ severity: 'success', summary: 'Deleted', detail: 'Branch deleted.', life: 3000 });
        await fetchBranches();
    } catch {
        toast.add({ severity: 'error', summary: 'Error', detail: 'Failed to delete branch.', life: 4000 });
    }
};

// --- Staff CRUD ---
const openStaffPanel = (branchData) => {
    viewStaffBranchId.value = branchData.id;
    showStaffPanel.value = true;
};

const addStaff = () => {
    staffMember.value = { ...emptyStaff };
    isEditingStaff.value = false;
    staffSubmitted.value = false;
    staffDialog.value = true;
};

const editStaff = (s) => {
    staffMember.value = { ...s };
    isEditingStaff.value = true;
    staffSubmitted.value = false;
    staffDialog.value = true;
};

const confirmDeleteStaff = (s) => {
    selectedStaff.value = s;
    deleteStaffDialog.value = true;
};

const saveStaff = async () => {
    staffSubmitted.value = true;

    if (!staffMember.value.name.trim() || !staffMember.value.designation.trim() || !staffMember.value.number.trim()) return;
    if (!isValidPhone(staffMember.value.number)) return;
    if (staffMember.value.email && !isValidEmail(staffMember.value.email)) return;

    const br = branches.value.find((b) => b.id === viewStaffBranchId.value);
    if (!br) return;

    // Update local staff list first
    if (isEditingStaff.value) {
        const idx = br.staff.findIndex((s) => s.id === staffMember.value.id);
        if (idx !== -1) br.staff[idx] = { ...staffMember.value };
    } else {
        br.staff.push({ ...staffMember.value, id: null });
    }

    // Persist via branch update
    try {
        const payload = mapToApi(br);
        await api.put(`/branches/${br.id}/`, payload);
        staffDialog.value = false;
        toast.add({ severity: 'success', summary: isEditingStaff.value ? 'Updated' : 'Added', detail: `Staff member ${isEditingStaff.value ? 'updated' : 'added'}.`, life: 3000 });
        await fetchBranches();
        // Re-point the staff panel to refreshed data
        viewStaffBranchId.value = br.id;
    } catch {
        toast.add({ severity: 'error', summary: 'Error', detail: 'Failed to save staff member.', life: 4000 });
        await fetchBranches();
    }
};

const deleteStaffConfirmed = async () => {
    const br = branches.value.find((b) => b.id === viewStaffBranchId.value);
    if (br) {
        br.staff = br.staff.filter((s) => s.id !== selectedStaff.value.id);
        try {
            const payload = mapToApi(br);
            await api.put(`/branches/${br.id}/`, payload);
            deleteStaffDialog.value = false;
            selectedStaff.value = null;
            toast.add({ severity: 'success', summary: 'Deleted', detail: 'Staff member removed.', life: 3000 });
            await fetchBranches();
            viewStaffBranchId.value = br.id;
        } catch {
            toast.add({ severity: 'error', summary: 'Error', detail: 'Failed to remove staff member.', life: 4000 });
            await fetchBranches();
        }
    }
};

const formatAddress = (addr) => {
    if (!addr) return '';
    return [addr.flat, addr.street, addr.suburb, addr.state, addr.postalCode, addr.country].filter(Boolean).join(', ');
};
</script>

<template>
    <Toast />
    <div class="card">
        <div class="font-semibold text-xl mb-4">Branch Management</div>

        <!-- Filter Bar -->
        <div class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3 mb-4">
            <Select v-model="filterCompany" :options="companies" optionLabel="name" optionValue="id" placeholder="Company" :showClear="true" class="w-full" @change="onFilterChange" />
            <InputText v-model="filterBranchName" placeholder="Branch Name" class="w-full" @input="onFilterChange" />
            <InputText v-model="filterPhone" placeholder="Phone" class="w-full" @input="onFilterChange" />
            <InputText v-model="filterAddress" placeholder="Address" class="w-full" @input="onFilterChange" />
            <InputText v-model="filterState" placeholder="State" class="w-full" @input="onFilterChange" />
            <div class="flex gap-2">
                <InputText v-model="filterSuburb" placeholder="Suburb" class="w-full" @input="onFilterChange" />
                <Button icon="pi pi-filter-slash" severity="secondary" outlined @click="clearFilters" v-tooltip.top="'Clear filters'" />
            </div>
        </div>

        <DataTable :value="branches" :paginator="true" :rows="rowsPerPage" :totalRecords="totalRecords" :lazy="true" :loading="loading" :rowHover="true" :rowsPerPageOptions="[10, 25, 50]" dataKey="id" responsiveLayout="scroll" @page="onPage" @sort="onSort" :sortField="sortField" :sortOrder="sortOrder">
            <template #header>
                <div class="flex justify-between items-center">
                    <span class="text-xl text-surface-900 dark:text-surface-0 font-bold">Branches</span>
                    <Button label="Add Branch" icon="pi pi-plus" size="small" @click="openNew" />
                </div>
            </template>
            <template #empty> No branches found. </template>
            <Column field="name" header="Branch Name" sortable style="min-width: 12rem"></Column>
            <Column field="companyName" header="Company" sortable style="min-width: 12rem"></Column>
            <Column header="Address" sortable style="min-width: 16rem">
                <template #body="{ data }">{{ formatAddress(data.address) }}</template>
            </Column>
            <Column field="managerNumber" header="Front Desk No." sortable style="min-width: 10rem"></Column>
            <Column field="storeNumber" header="Store No." sortable style="min-width: 8rem"></Column>
            <Column header="Staff" style="min-width: 8rem">
                <template #body="{ data }">
                    <Button :label="`${data.staff.length} staff`" icon="pi pi-users" size="small" text @click="openStaffPanel(data)" />
                </template>
            </Column>
            <Column header="Actions" style="min-width: 10rem">
                <template #body="{ data }">
                    <div class="flex gap-2">
                        <Button icon="pi pi-pencil" rounded outlined severity="info" size="small" @click="editBranch(data)" />
                        <Button icon="pi pi-trash" rounded outlined severity="danger" size="small" @click="confirmDelete(data)" />
                    </div>
                </template>
            </Column>
        </DataTable>
    </div>

    <!-- Branch Dialog -->
    <Dialog v-model:visible="branchDialog" :header="isEditing ? 'Edit Branch' : 'Add Branch'" :modal="true" :style="{ width: '700px' }">
        <form @submit.prevent="saveBranch">
            <div class="flex flex-col gap-6 mt-4">
                <div class="flex flex-col gap-2">
                    <label class="font-medium">Company *</label>
                    <Select v-model="branch.companyId" :options="companies" optionLabel="name" optionValue="id" placeholder="Select a company" :invalid="submitted && !branch.companyId" />
                    <small v-if="submitted && !branch.companyId" class="text-red-500">Please select a company.</small>
                </div>

                <div class="flex flex-col gap-2">
                    <label class="font-medium">Branch Name *</label>
                    <InputText v-model="branch.name" :invalid="submitted && !branch.name.trim()" placeholder="Enter branch name" />
                    <small v-if="submitted && !branch.name.trim()" class="text-red-500">Branch name is required.</small>
                </div>

                <!-- Google Address Section -->
                <div class="flex flex-col gap-4">
                    <label class="font-medium">Address *</label>
                    <AutoComplete v-model="branch.address.full" :suggestions="addressSuggestions" optionLabel="full" placeholder="Search address from Google..." @complete="searchAddress" @item-select="onAddressSelect" forceSelection:false class="w-full" />
                    <small class="text-muted-color -mt-2"><i class="pi pi-map-marker mr-1"></i>Select from Google Places or fill manually below</small>

                    <div class="grid grid-cols-2 gap-4">
                        <div class="flex flex-col gap-2">
                            <label class="text-sm">Flat / House No.</label>
                            <InputText v-model="branch.address.flat" placeholder="Flat / House No." />
                        </div>
                        <div class="flex flex-col gap-2">
                            <label class="text-sm">Street *</label>
                            <InputText v-model="branch.address.street" :invalid="submitted && !branch.address.street.trim()" placeholder="Street" />
                            <small v-if="submitted && !branch.address.street.trim()" class="text-red-500">Street is required.</small>
                        </div>
                    </div>
                    <div class="grid grid-cols-2 gap-4">
                        <div class="flex flex-col gap-2">
                            <label class="text-sm">Suburb</label>
                            <InputText v-model="branch.address.suburb" placeholder="Suburb" />
                        </div>
                        <div class="flex flex-col gap-2">
                            <label class="text-sm">Postal Code</label>
                            <InputText v-model="branch.address.postalCode" placeholder="Postal Code" />
                        </div>
                    </div>
                    <div class="grid grid-cols-2 gap-4">
                        <div class="flex flex-col gap-2">
                            <label class="text-sm">State</label>
                            <InputText v-model="branch.address.state" placeholder="State" />
                        </div>
                        <div class="flex flex-col gap-2">
                            <label class="text-sm">Country</label>
                            <InputText v-model="branch.address.country" placeholder="Country" />
                        </div>
                    </div>
                </div>

                <div class="flex flex-col gap-2">
                    <label class="font-medium">Front Desk / Reception Number *</label>
                    <InputText v-model="branch.managerNumber" :invalid="submitted && (!branch.managerNumber.trim() || !isValidPhone(branch.managerNumber))" placeholder="+1-212-555-0100" />
                    <small v-if="submitted && !branch.managerNumber.trim()" class="text-red-500">Front desk number is required.</small>
                    <small v-else-if="submitted && !isValidPhone(branch.managerNumber)" class="text-red-500">Enter a valid phone number.</small>
                </div>

                <div class="flex flex-col gap-2">
                    <label class="font-medium">Store Number *</label>
                    <InputText v-model="branch.storeNumber" :invalid="submitted && !branch.storeNumber.trim()" placeholder="STR-001" />
                    <small v-if="submitted && !branch.storeNumber.trim()" class="text-red-500">Store number is required.</small>
                </div>
            </div>

            <div class="flex justify-end gap-2 mt-6">
                <Button label="Cancel" icon="pi pi-times" severity="secondary" @click="branchDialog = false" type="button" />
                <Button type="submit" :label="isEditing ? 'Update' : 'Save'" icon="pi pi-check" />
            </div>
        </form>
    </Dialog>

    <!-- Staff Panel Dialog -->
    <Dialog v-model:visible="showStaffPanel" :header="`Staff — ${viewStaffBranch?.name || ''}`" :modal="true" :style="{ width: '750px' }">
        <DataTable :value="viewStaffBranch?.staff || []" dataKey="id" :rowHover="true" responsiveLayout="scroll">
            <template #header>
                <div class="flex justify-between items-center">
                    <span class="font-semibold">Staff Members</span>
                    <Button label="Add Staff" icon="pi pi-plus" size="small" @click="addStaff" />
                </div>
            </template>
            <template #empty> No staff members. </template>
            <Column field="name" header="Name" style="min-width: 12rem"></Column>
            <Column field="designation" header="Designation" style="min-width: 10rem"></Column>
            <Column field="email" header="Email" style="min-width: 14rem"></Column>
            <Column field="number" header="Phone Number" style="min-width: 10rem"></Column>
            <Column header="Actions" style="min-width: 8rem">
                <template #body="{ data }">
                    <div class="flex gap-2">
                        <Button icon="pi pi-pencil" rounded outlined severity="info" size="small" @click="editStaff(data)" />
                        <Button icon="pi pi-trash" rounded outlined severity="danger" size="small" @click="confirmDeleteStaff(data)" />
                    </div>
                </template>
            </Column>
        </DataTable>
    </Dialog>

    <!-- Staff Add/Edit Dialog -->
    <Dialog v-model:visible="staffDialog" :header="isEditingStaff ? 'Edit Staff' : 'Add Staff'" :modal="true" :style="{ width: '450px' }">
        <form @submit.prevent="saveStaff">
            <div class="flex flex-col gap-6 mt-4">
                <div class="flex flex-col gap-2">
                    <label class="font-medium">Name *</label>
                    <InputText v-model="staffMember.name" :invalid="staffSubmitted && !staffMember.name.trim()" placeholder="Staff name" />
                    <small v-if="staffSubmitted && !staffMember.name.trim()" class="text-red-500">Name is required.</small>
                </div>

                <div class="flex flex-col gap-2">
                    <label class="font-medium">Designation *</label>
                    <InputText v-model="staffMember.designation" :invalid="staffSubmitted && !staffMember.designation.trim()" placeholder="Designation" />
                    <small v-if="staffSubmitted && !staffMember.designation.trim()" class="text-red-500">Designation is required.</small>
                </div>

                <div class="flex flex-col gap-2">
                    <label class="font-medium">Email</label>
                    <InputText v-model="staffMember.email" type="email" :invalid="staffSubmitted && staffMember.email && !isValidEmail(staffMember.email)" placeholder="staff@company.com" />
                    <small v-if="staffSubmitted && staffMember.email && !isValidEmail(staffMember.email)" class="text-red-500">Enter a valid email address.</small>
                </div>

                <div class="flex flex-col gap-2">
                    <label class="font-medium">Phone Number *</label>
                    <InputText v-model="staffMember.number" :invalid="staffSubmitted && (!staffMember.number.trim() || !isValidPhone(staffMember.number))" placeholder="+1-555-0100" />
                    <small v-if="staffSubmitted && !staffMember.number.trim()" class="text-red-500">Phone number is required.</small>
                    <small v-else-if="staffSubmitted && !isValidPhone(staffMember.number)" class="text-red-500">Enter a valid phone number.</small>
                </div>
            </div>

            <div class="flex justify-end gap-2 mt-6">
                <Button label="Cancel" icon="pi pi-times" severity="secondary" @click="staffDialog = false" type="button" />
                <Button type="submit" :label="isEditingStaff ? 'Update' : 'Add'" icon="pi pi-check" />
            </div>
        </form>
    </Dialog>

    <!-- Delete Branch Confirmation -->
    <Dialog v-model:visible="deleteDialog" header="Confirm Delete" :modal="true" :style="{ width: '400px' }">
        <div class="flex items-center gap-4">
            <i class="pi pi-exclamation-triangle text-3xl text-red-500" />
            <span>Are you sure you want to delete <strong>{{ selectedBranch?.name }}</strong>?</span>
        </div>
        <template #footer>
            <div class="flex justify-end gap-2">
                <Button label="No" icon="pi pi-times" severity="secondary" @click="deleteDialog = false" />
                <Button label="Yes" icon="pi pi-check" severity="danger" @click="deleteBranchConfirmed" />
            </div>
        </template>
    </Dialog>

    <!-- Delete Staff Confirmation -->
    <Dialog v-model:visible="deleteStaffDialog" header="Confirm Delete" :modal="true" :style="{ width: '400px' }">
        <div class="flex items-center gap-4">
            <i class="pi pi-exclamation-triangle text-3xl text-red-500" />
            <span>Remove <strong>{{ selectedStaff?.name }}</strong> from staff?</span>
        </div>
        <template #footer>
            <div class="flex justify-end gap-2">
                <Button label="No" icon="pi pi-times" severity="secondary" @click="deleteStaffDialog = false" />
                <Button label="Yes" icon="pi pi-check" severity="danger" @click="deleteStaffConfirmed" />
            </div>
        </template>
    </Dialog>
</template>
