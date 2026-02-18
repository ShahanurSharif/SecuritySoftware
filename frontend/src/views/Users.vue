<script setup>
import { ref, computed, onMounted } from 'vue';
import { useToast } from 'primevue/usetoast';
import api from '@/services/api';
import AddressField from '@/components/AddressField.vue';

const toast = useToast();
const loading = ref(false);

const users = ref([]);
const totalRecords = ref(0);
const currentPage = ref(1);
const rowsPerPage = ref(10);
const sortField = ref('user__first_name');
const sortOrder = ref(1);
const filterText = ref('');

const userDialog = ref(false);
const deleteDialog = ref(false);
const roleDialog = ref(false);
const isEditing = ref(false);
const submitted = ref(false);

const groupOptions = ref([
    { label: 'Admin', value: 'Admin' },
    { label: 'Manager', value: 'Manager' },
    { label: 'Analyst', value: 'Analyst' },
    { label: 'LPO', value: 'LPO' },
    { label: 'Viewer', value: 'Viewer' }
]);

const emptyUser = {
    id: null,
    firstName: '',
    lastName: '',
    email: '',
    password: '',
    birthday: null,
    phone: '',
    address: { full: '', flat: '', street: '', suburb: '', postalCode: '', state: '', country: '' },
    group: null,
    photo: null,
    photoId: null,
    role: 'LPO',
    status: 'Active'
};
const user = ref({ ...emptyUser });
const selectedUser = ref(null);
const photoPreview = ref(null);
const photoFile = ref(null);

const isValidPhone = (val) => /^[+]?[\d\s()-]{7,20}$/.test(val);
const isValidEmail = (val) => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(val);

const age = computed(() => {
    if (!user.value.birthday) return null;
    const birth = new Date(user.value.birthday);
    const today = new Date();
    let a = today.getFullYear() - birth.getFullYear();
    const m = today.getMonth() - birth.getMonth();
    if (m < 0 || (m === 0 && today.getDate() < birth.getDate())) a--;
    return a;
});

const getRoleSeverity = (role) => {
    const map = { Admin: 'danger', LPO: 'info' };
    return map[role] || 'secondary';
};

const formatDate = (date) => {
    if (!date) return '';
    const d = new Date(date);
    return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
};

// --- Map API response to frontend shape ---
const mapFromApi = (p) => ({
    id: p.id,
    firstName: p.first_name || '',
    lastName: p.last_name || '',
    email: p.email || '',
    phone: p.phone || '',
    birthday: p.birthday || null,
    role: p.role || 'LPO',
    group: p.group || 'Viewer',
    status: p.status || 'Active',
    lastLogin: p.last_login ? new Date(p.last_login).toLocaleString() : 'Never',
    photo: p.photo?.file_url || null,
    photoId: p.photo?.id || null,
    address: p.address
        ? {
              full: [p.address.flat, p.address.street, p.address.suburb, p.address.state, p.address.postal_code, p.address.country].filter(Boolean).join(', '),
              flat: p.address.flat || '',
              street: p.address.street || '',
              suburb: p.address.suburb || '',
              postalCode: p.address.postal_code || '',
              state: p.address.state || '',
              country: p.address.country || ''
          }
        : { full: '', flat: '', street: '', suburb: '', postalCode: '', state: '', country: '' }
});

// --- Upload photo to /media/ endpoint, returns media ID ---
const uploadPhoto = async (file) => {
    const fd = new FormData();
    fd.append('file', file);
    fd.append('file_type', 'photo');
    const { data } = await api.post('/media/', fd, {
        headers: { 'Content-Type': 'multipart/form-data' }
    });
    return data.id;
};

// --- Fetch users (server-side pagination, search, ordering) ---
const fetchUsers = async () => {
    loading.value = true;
    try {
        const params = { page: currentPage.value, page_size: rowsPerPage.value };
        if (filterText.value.trim()) params.search = filterText.value.trim();
        if (sortField.value) {
            params.ordering = sortOrder.value === 1 ? sortField.value : `-${sortField.value}`;
        }
        const { data } = await api.get('/profiles/', { params });
        users.value = (data.results || []).map(mapFromApi);
        totalRecords.value = data.count || 0;
    } catch {
        toast.add({ severity: 'error', summary: 'Error', detail: 'Failed to load users.', life: 4000 });
    } finally {
        loading.value = false;
    }
};

onMounted(fetchUsers);

// --- Server-side event handlers ---
const onPage = (event) => {
    currentPage.value = event.page + 1;
    rowsPerPage.value = event.rows;
    fetchUsers();
};

const onSort = (event) => {
    sortField.value = event.sortField;
    sortOrder.value = event.sortOrder;
    currentPage.value = 1;
    fetchUsers();
};

let searchTimeout = null;
const onSearch = () => {
    clearTimeout(searchTimeout);
    searchTimeout = setTimeout(() => {
        currentPage.value = 1;
        fetchUsers();
    }, 400);
};

const openNew = () => {
    user.value = { ...emptyUser, address: { ...emptyUser.address } };
    photoPreview.value = null;
    photoFile.value = null;
    isEditing.value = false;
    submitted.value = false;
    userDialog.value = true;
};

const editUser = (data) => {
    user.value = { ...data, address: { ...data.address }, birthday: data.birthday ? new Date(data.birthday) : null, password: '' };
    photoPreview.value = data.photo;
    photoFile.value = null;
    isEditing.value = true;
    submitted.value = false;
    userDialog.value = true;
};

const confirmDelete = (data) => {
    selectedUser.value = data;
    deleteDialog.value = true;
};

const onPhotoSelect = (event) => {
    const file = event.files?.[0];
    if (file) {
        photoFile.value = file;
        const reader = new FileReader();
        reader.onload = (e) => {
            photoPreview.value = e.target.result;
        };
        reader.readAsDataURL(file);
    }
};

const onPhotoRemove = () => {
    photoPreview.value = null;
    photoFile.value = null;
    user.value.photo = null;
    user.value.photoId = null;
};

const saveUser = async () => {
    submitted.value = true;

    if (!user.value.firstName.trim() || !user.value.lastName.trim()) return;
    if (!user.value.email.trim() || !isValidEmail(user.value.email)) return;
    if (!isEditing.value && (!user.value.password || user.value.password.length < 6)) return;
    if (!user.value.phone.trim() || !isValidPhone(user.value.phone)) return;
    if (!user.value.birthday) return;
    if (!user.value.group) return;

    const fullName = `${user.value.firstName} ${user.value.lastName}`;

    try {
        // Upload photo first if a new file was selected
        let photoId = user.value.photoId || null;
        if (photoFile.value) {
            photoId = await uploadPhoto(photoFile.value);
        }

        const payload = {
            first_name: user.value.firstName,
            last_name: user.value.lastName,
            email: user.value.email,
            phone: user.value.phone || '',
            birthday: user.value.birthday ? formatDate(user.value.birthday) : null,
            role: user.value.role || 'LPO',
            group: user.value.group || 'Viewer',
            status: user.value.status || 'Active',
            photo_id: photoId,
            address: {
                flat: user.value.address.flat || '',
                street: user.value.address.street || '',
                suburb: user.value.address.suburb || '',
                postal_code: user.value.address.postalCode || '',
                state: user.value.address.state || '',
                country: user.value.address.country || ''
            }
        };
        if (user.value.password) payload.password = user.value.password;

        if (isEditing.value) {
            await api.put(`/profiles/${user.value.id}/`, payload);
            toast.add({ severity: 'success', summary: 'Updated', detail: `${fullName} updated.`, life: 3000 });
        } else {
            await api.post('/profiles/', payload);
            toast.add({ severity: 'success', summary: 'Created', detail: `${fullName} created.`, life: 3000 });
        }

        userDialog.value = false;
        fetchUsers();
    } catch (err) {
        const detail = err.response?.data?.email?.[0] || err.response?.data?.detail || 'Failed to save user.';
        toast.add({ severity: 'error', summary: 'Error', detail, life: 4000 });
    }
};

const deleteUserConfirmed = async () => {
    try {
        await api.delete(`/profiles/${selectedUser.value.id}/`);
        deleteDialog.value = false;
        selectedUser.value = null;
        toast.add({ severity: 'success', summary: 'Deleted', detail: 'User deleted.', life: 3000 });
        fetchUsers();
    } catch {
        toast.add({ severity: 'error', summary: 'Error', detail: 'Failed to delete user.', life: 4000 });
    }
};

const roleOptions = ['Admin', 'LPO'];
const selectedRoleUser = ref(null);
const selectedNewRole = ref(null);

const openRoleDialog = (data) => {
    selectedRoleUser.value = data;
    selectedNewRole.value = data.role;
    roleDialog.value = true;
};

const saveRoleChange = async () => {
    if (!selectedNewRole.value) return;
    try {
        await api.patch(`/profiles/${selectedRoleUser.value.id}/role/`, { role: selectedNewRole.value });
        toast.add({ severity: 'success', summary: 'Role Updated', detail: `${selectedRoleUser.value.firstName} ${selectedRoleUser.value.lastName} is now ${selectedNewRole.value}.`, life: 3000 });
        roleDialog.value = false;
        fetchUsers();
    } catch {
        toast.add({ severity: 'error', summary: 'Error', detail: 'Failed to update role.', life: 4000 });
    }
};
</script>

<template>
    <Toast />
    <div class="card">
        <div class="font-semibold text-xl mb-4">User Management</div>
        <DataTable :value="users" :paginator="true" :rows="rowsPerPage" :totalRecords="totalRecords" :loading="loading" :lazy="true" dataKey="id" :rowHover="true" responsiveLayout="scroll" @page="onPage" @sort="onSort">
            <template #header>
                <div class="flex justify-between items-center">
                    <span class="text-xl text-surface-900 dark:text-surface-0 font-bold">Users</span>
                    <div class="flex gap-2">
                        <InputText v-model="filterText" placeholder="Search users..." @input="onSearch" class="w-64" />
                        <Button label="Add User" icon="pi pi-plus" size="small" @click="openNew" />
                    </div>
                </div>
            </template>
            <template #empty> No users found. </template>
            <Column header="Photo" style="min-width: 5rem">
                <template #body="{ data }">
                    <img v-if="data.photo" :src="data.photo" class="w-10 h-10 rounded-full object-cover" alt="photo" />
                    <div v-else class="w-10 h-10 rounded-full bg-surface-200 dark:bg-surface-700 flex items-center justify-center">
                        <i class="pi pi-user text-surface-500"></i>
                    </div>
                </template>
            </Column>
            <Column header="Name" sortable sortField="user__first_name" style="min-width: 12rem">
                <template #body="{ data }">{{ data.firstName }} {{ data.lastName }}</template>
            </Column>
            <Column field="email" header="Email" sortable sortField="user__email" style="min-width: 14rem"></Column>
            <Column field="role" header="Role" sortable sortField="role" style="min-width: 8rem">
                <template #body="{ data }">
                    <Tag :value="data.role" :severity="getRoleSeverity(data.role)" />
                </template>
            </Column>
            <Column field="group" header="Group" sortable sortField="group" style="min-width: 8rem"></Column>
            <Column field="status" header="Status" sortable sortField="status" style="min-width: 8rem">
                <template #body="{ data }">
                    <Tag :value="data.status" :severity="data.status === 'Active' ? 'success' : 'secondary'" />
                </template>
            </Column>
            <Column field="lastLogin" header="Last Login" sortable sortField="user__last_login" style="min-width: 12rem"></Column>
            <Column header="Actions" style="min-width: 12rem">
                <template #body="{ data }">
                    <div class="flex gap-2">
                        <Button icon="pi pi-shield" rounded outlined severity="warn" size="small" @click="openRoleDialog(data)" v-tooltip.top="'Change Role'" />
                        <Button icon="pi pi-pencil" rounded outlined severity="info" size="small" @click="editUser(data)" />
                        <Button icon="pi pi-trash" rounded outlined severity="danger" size="small" @click="confirmDelete(data)" />
                    </div>
                </template>
            </Column>
        </DataTable>
    </div>

    <!-- Add/Edit User Dialog -->
    <Dialog v-model:visible="userDialog" :header="isEditing ? 'Edit User' : 'Add User'" :modal="true" :style="{ width: '650px' }">
        <form @submit.prevent="saveUser">
            <div class="flex flex-col gap-6 mt-4">
                <!-- Photo Upload -->
                <div class="flex flex-col gap-2">
                    <label class="font-medium">Photo</label>
                    <div class="flex items-center gap-4">
                        <div v-if="photoPreview" class="relative">
                            <img :src="photoPreview" class="w-20 h-20 rounded-full object-cover" alt="preview" />
                            <Button icon="pi pi-times" rounded text severity="danger" size="small" class="absolute -top-2 -right-2" @click="onPhotoRemove" type="button" />
                        </div>
                        <FileUpload mode="basic" accept="image/*" :maxFileSize="2000000" chooseLabel="Upload Photo" :auto="false" @select="onPhotoSelect" class="p-button-outlined" />
                    </div>
                </div>

                <div class="grid grid-cols-2 gap-4">
                    <div class="flex flex-col gap-2">
                        <label class="font-medium">First Name *</label>
                        <InputText v-model="user.firstName" :invalid="submitted && !user.firstName.trim()" placeholder="First name" />
                        <small v-if="submitted && !user.firstName.trim()" class="text-red-500">First name is required.</small>
                    </div>

                    <div class="flex flex-col gap-2">
                        <label class="font-medium">Last Name *</label>
                        <InputText v-model="user.lastName" :invalid="submitted && !user.lastName.trim()" placeholder="Last name" />
                        <small v-if="submitted && !user.lastName.trim()" class="text-red-500">Last name is required.</small>
                    </div>
                </div>

                <div class="grid grid-cols-2 gap-4">
                    <div class="flex flex-col gap-2">
                        <label class="font-medium">Birthday *</label>
                        <DatePicker v-model="user.birthday" dateFormat="dd/mm/yy" :showIcon="true" :showButtonBar="true" placeholder="dd/mm/yyyy" :invalid="submitted && !user.birthday" :maxDate="new Date()" />
                        <small v-if="submitted && !user.birthday" class="text-red-500">Birthday is required.</small>
                    </div>

                    <div class="flex flex-col gap-2">
                        <label class="font-medium">Age</label>
                        <InputText :modelValue="age !== null ? `${age} years` : ''" disabled placeholder="Auto-calculated" />
                    </div>
                </div>

                <div class="flex flex-col gap-2">
                    <label class="font-medium">Email *</label>
                    <InputText v-model="user.email" type="email" :invalid="submitted && (!user.email.trim() || !isValidEmail(user.email))" placeholder="user@example.com" />
                    <small v-if="submitted && !user.email.trim()" class="text-red-500">Email is required.</small>
                    <small v-else-if="submitted && !isValidEmail(user.email)" class="text-red-500">Enter a valid email address.</small>
                </div>

                <div class="flex flex-col gap-2">
                    <label class="font-medium">Password {{ isEditing ? '(leave blank to keep)' : '*' }}</label>
                    <Password v-model="user.password" :invalid="submitted && !isEditing && (!user.password || user.password.length < 6)" placeholder="Password" :toggleMask="true" fluid :feedback="true" />
                    <small v-if="submitted && !isEditing && (!user.password || user.password.length < 6)" class="text-red-500">Password must be at least 6 characters.</small>
                </div>

                <div class="flex flex-col gap-2">
                    <label class="font-medium">Phone Number *</label>
                    <InputText v-model="user.phone" :invalid="submitted && (!user.phone.trim() || !isValidPhone(user.phone))" placeholder="+1-212-555-0100" />
                    <small v-if="submitted && !user.phone.trim()" class="text-red-500">Phone number is required.</small>
                    <small v-else-if="submitted && !isValidPhone(user.phone)" class="text-red-500">Enter a valid phone number.</small>
                </div>

                <AddressField v-model="user.address" :submitted="submitted" label="Address" :requireStreet="false" />

                <div class="flex flex-col gap-2">
                    <label class="font-medium">Group *</label>
                    <Select v-model="user.group" :options="groupOptions" optionLabel="label" optionValue="value" placeholder="Select a group" :invalid="submitted && !user.group" />
                    <small v-if="submitted && !user.group" class="text-red-500">Group is required.</small>
                </div>
            </div>

            <div class="flex justify-end gap-2 mt-6">
                <Button label="Cancel" icon="pi pi-times" severity="secondary" @click="userDialog = false" type="button" />
                <Button type="submit" :label="isEditing ? 'Update' : 'Save'" icon="pi pi-check" />
            </div>
        </form>
    </Dialog>

    <!-- Delete Confirmation -->
    <Dialog v-model:visible="deleteDialog" header="Confirm Delete" :modal="true" :style="{ width: '400px' }">
        <div class="flex items-center gap-4">
            <i class="pi pi-exclamation-triangle text-3xl text-red-500" />
            <span>Are you sure you want to delete <strong>{{ selectedUser?.firstName }} {{ selectedUser?.lastName }}</strong>?</span>
        </div>
        <template #footer>
            <div class="flex justify-end gap-2">
                <Button label="No" icon="pi pi-times" severity="secondary" @click="deleteDialog = false" />
                <Button label="Yes" icon="pi pi-check" severity="danger" @click="deleteUserConfirmed" />
            </div>
        </template>
    </Dialog>

    <!-- Role Change Dialog -->
    <Dialog v-model:visible="roleDialog" header="Change Role" :modal="true" :style="{ width: '400px' }">
        <div class="flex flex-col gap-4 mt-2">
            <div class="text-sm text-muted-color">Changing role for <strong>{{ selectedRoleUser?.firstName }} {{ selectedRoleUser?.lastName }}</strong></div>
            <div class="flex flex-col gap-2">
                <label class="font-medium">Role</label>
                <Select v-model="selectedNewRole" :options="roleOptions" placeholder="Select role" />
            </div>
        </div>
        <template #footer>
            <div class="flex justify-end gap-2">
                <Button label="Cancel" icon="pi pi-times" severity="secondary" @click="roleDialog = false" />
                <Button label="Save" icon="pi pi-check" @click="saveRoleChange" />
            </div>
        </template>
    </Dialog>
</template>
