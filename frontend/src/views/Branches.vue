<script setup>
import { ref, computed } from 'vue';
import { useToast } from 'primevue/usetoast';

const toast = useToast();

const companies = ref([
    { id: 1, name: 'SecureCorp Ltd.' },
    { id: 2, name: 'CyberShield Inc.' }
]);

const branches = ref([
    {
        id: 1,
        companyId: 1,
        companyName: 'SecureCorp Ltd.',
        name: 'Downtown Branch',
        address: { full: '789 Broadway, New York, NY 10003', flat: '789', street: 'Broadway', suburb: 'NoHo', postalCode: '10003', state: 'NY', country: 'US' },
        managerNumber: '+1-212-555-0301',
        storeNumber: 'STR-001',
        staff: [
            { id: 1, name: 'Alice Johnson', designation: 'Security Analyst', number: '+1-212-555-1001', email: 'alice@securecorp.com' },
            { id: 2, name: 'Bob Martinez', designation: 'Guard', number: '+1-212-555-1002', email: 'bob@securecorp.com' }
        ]
    },
    {
        id: 2,
        companyId: 2,
        companyName: 'CyberShield Inc.',
        name: 'Bay Area Office',
        address: { full: '321 Mission St, San Francisco, CA 94105', flat: '321', street: 'Mission St', suburb: 'SoMa', postalCode: '94105', state: 'CA', country: 'US' },
        managerNumber: '+1-415-555-0401',
        storeNumber: 'STR-002',
        staff: [
            { id: 1, name: 'Carol Lee', designation: 'Branch Manager', number: '+1-415-555-2001', email: 'carol@cybershield.com' }
        ]
    }
]);

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

let nextId = 3;
let nextStaffId = 10;

const isValidPhone = (val) => /^[+]?[\d\s()-]{7,20}$/.test(val);
const isValidEmail = (val) => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(val);

// --- Filtered branches ---
const filteredBranches = computed(() => {
    return branches.value.filter((b) => {
        if (filterCompany.value && b.companyId !== filterCompany.value) return false;
        if (filterBranchName.value && !b.name.toLowerCase().includes(filterBranchName.value.toLowerCase())) return false;
        if (filterPhone.value && !b.managerNumber.toLowerCase().includes(filterPhone.value.toLowerCase())) return false;
        const addrStr = [b.address.full, b.address.flat, b.address.street, b.address.suburb, b.address.postalCode, b.address.state, b.address.country].filter(Boolean).join(' ').toLowerCase();
        if (filterAddress.value && !addrStr.includes(filterAddress.value.toLowerCase())) return false;
        if (filterState.value && !(b.address.state || '').toLowerCase().includes(filterState.value.toLowerCase())) return false;
        if (filterSuburb.value && !(b.address.suburb || '').toLowerCase().includes(filterSuburb.value.toLowerCase())) return false;
        return true;
    });
});

const clearFilters = () => {
    filterCompany.value = null;
    filterBranchName.value = '';
    filterPhone.value = '';
    filterAddress.value = '';
    filterState.value = '';
    filterSuburb.value = '';
};

// --- Google Places autocomplete stub ---
const addressSuggestions = ref([]);

const searchAddress = (event) => {
    const query = event.query;
    // TODO: Replace with real Google Places API call
    setTimeout(() => {
        addressSuggestions.value = [
            { full: `${query}, Suburb, State 00000, Country`, flat: '', street: query, suburb: 'Suburb', postalCode: '00000', state: 'State', country: 'Country' }
        ];
    }, 300);
};

const onAddressSelect = (event) => {
    const selected = event.value;
    if (selected && typeof selected === 'object') {
        branch.value.address = { ...selected };
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

const saveBranch = () => {
    submitted.value = true;

    if (!branch.value.companyId || !branch.value.name.trim() || !branch.value.address.street.trim() || !branch.value.managerNumber.trim() || !branch.value.storeNumber.trim()) return;
    if (!isValidPhone(branch.value.managerNumber)) return;

    const comp = companies.value.find((c) => c.id === branch.value.companyId);
    branch.value.companyName = comp ? comp.name : '';

    if (isEditing.value) {
        const idx = branches.value.findIndex((b) => b.id === branch.value.id);
        if (idx !== -1) branches.value[idx] = { ...branch.value, address: { ...branch.value.address }, staff: branch.value.staff.map((s) => ({ ...s })) };
        toast.add({ severity: 'success', summary: 'Updated', detail: 'Branch updated successfully.', life: 3000 });
    } else {
        branch.value.id = nextId++;
        branches.value.push({ ...branch.value, address: { ...branch.value.address }, staff: branch.value.staff.map((s) => ({ ...s })) });
        toast.add({ severity: 'success', summary: 'Created', detail: 'Branch created successfully.', life: 3000 });
    }
    branchDialog.value = false;
};

const deleteBranchConfirmed = () => {
    branches.value = branches.value.filter((b) => b.id !== selectedBranch.value.id);
    deleteDialog.value = false;
    selectedBranch.value = null;
    toast.add({ severity: 'success', summary: 'Deleted', detail: 'Branch deleted.', life: 3000 });
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

const saveStaff = () => {
    staffSubmitted.value = true;

    if (!staffMember.value.name.trim() || !staffMember.value.designation.trim() || !staffMember.value.number.trim()) return;
    if (!isValidPhone(staffMember.value.number)) return;
    if (staffMember.value.email && !isValidEmail(staffMember.value.email)) return;

    const br = branches.value.find((b) => b.id === viewStaffBranchId.value);
    if (!br) return;

    if (isEditingStaff.value) {
        const idx = br.staff.findIndex((s) => s.id === staffMember.value.id);
        if (idx !== -1) br.staff[idx] = { ...staffMember.value };
        toast.add({ severity: 'success', summary: 'Updated', detail: 'Staff member updated.', life: 3000 });
    } else {
        staffMember.value.id = nextStaffId++;
        br.staff.push({ ...staffMember.value });
        toast.add({ severity: 'success', summary: 'Added', detail: 'Staff member added.', life: 3000 });
    }
    staffDialog.value = false;
};

const deleteStaffConfirmed = () => {
    const br = branches.value.find((b) => b.id === viewStaffBranchId.value);
    if (br) br.staff = br.staff.filter((s) => s.id !== selectedStaff.value.id);
    deleteStaffDialog.value = false;
    selectedStaff.value = null;
    toast.add({ severity: 'success', summary: 'Deleted', detail: 'Staff member removed.', life: 3000 });
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
            <Select v-model="filterCompany" :options="companies" optionLabel="name" optionValue="id" placeholder="Company" :showClear="true" class="w-full" />
            <InputText v-model="filterBranchName" placeholder="Branch Name" class="w-full" />
            <InputText v-model="filterPhone" placeholder="Phone" class="w-full" />
            <InputText v-model="filterAddress" placeholder="Address" class="w-full" />
            <InputText v-model="filterState" placeholder="State" class="w-full" />
            <div class="flex gap-2">
                <InputText v-model="filterSuburb" placeholder="Suburb" class="w-full" />
                <Button icon="pi pi-filter-slash" severity="secondary" outlined @click="clearFilters" v-tooltip.top="'Clear filters'" />
            </div>
        </div>

        <DataTable :value="filteredBranches" :paginator="true" :rows="10" dataKey="id" :rowHover="true" responsiveLayout="scroll">
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
