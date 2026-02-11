<script setup>
import { ref, computed } from 'vue';
import { useToast } from 'primevue/usetoast';

const toast = useToast();

const users = ref([
    { id: 1, firstName: 'Admin', lastName: 'User', email: 'admin@security.io', role: 'Admin', group: 'Admin', status: 'Active', lastLogin: '2026-02-10 08:00:00', birthday: '1990-01-15', phone: '+1-212-555-0100', address: 'New York, NY', photo: null },
    { id: 2, firstName: 'John', lastName: 'Doe', email: 'john.doe@security.io', role: 'Analyst', group: 'Analyst', status: 'Active', lastLogin: '2026-02-10 07:45:00', birthday: '1988-05-20', phone: '+1-415-555-0200', address: 'San Francisco, CA', photo: null },
    { id: 3, firstName: 'Jane', lastName: 'Smith', email: 'jane.smith@security.io', role: 'Analyst', group: 'LPO', status: 'Active', lastLogin: '2026-02-09 16:00:00', birthday: '1992-08-10', phone: '+1-312-555-0300', address: 'Chicago, IL', photo: null },
    { id: 4, firstName: 'Bob', lastName: 'Wilson', email: 'bob.wilson@security.io', role: 'Viewer', group: 'Viewer', status: 'Inactive', lastLogin: '2026-01-15 10:30:00', birthday: '1985-12-01', phone: '+1-713-555-0400', address: 'Houston, TX', photo: null }
]);

const userDialog = ref(false);
const deleteDialog = ref(false);
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
    address: '',
    group: null,
    photo: null,
    role: 'Viewer',
    status: 'Active'
};
const user = ref({ ...emptyUser });
const selectedUser = ref(null);
const photoPreview = ref(null);

let nextId = 5;

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
    const map = { Admin: 'danger', Analyst: 'info', Viewer: 'secondary' };
    return map[role] || 'secondary';
};

const openNew = () => {
    user.value = { ...emptyUser };
    photoPreview.value = null;
    isEditing.value = false;
    submitted.value = false;
    userDialog.value = true;
};

const editUser = (data) => {
    user.value = { ...data, birthday: data.birthday ? new Date(data.birthday) : null, password: '' };
    photoPreview.value = data.photo;
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
        const reader = new FileReader();
        reader.onload = (e) => {
            photoPreview.value = e.target.result;
            user.value.photo = e.target.result;
        };
        reader.readAsDataURL(file);
    }
};

const onPhotoRemove = () => {
    photoPreview.value = null;
    user.value.photo = null;
};

const saveUser = () => {
    submitted.value = true;

    if (!user.value.firstName.trim() || !user.value.lastName.trim()) return;
    if (!user.value.email.trim() || !isValidEmail(user.value.email)) return;
    if (!isEditing.value && (!user.value.password || user.value.password.length < 6)) return;
    if (!user.value.phone.trim() || !isValidPhone(user.value.phone)) return;
    if (!user.value.birthday) return;
    if (!user.value.group) return;

    const fullName = `${user.value.firstName} ${user.value.lastName}`;

    if (isEditing.value) {
        const idx = users.value.findIndex((u) => u.id === user.value.id);
        if (idx !== -1) {
            users.value[idx] = {
                ...user.value,
                birthday: user.value.birthday ? formatDate(user.value.birthday) : null
            };
        }
        toast.add({ severity: 'success', summary: 'Updated', detail: `${fullName} updated.`, life: 3000 });
    } else {
        user.value.id = nextId++;
        user.value.lastLogin = 'Never';
        users.value.push({
            ...user.value,
            birthday: user.value.birthday ? formatDate(user.value.birthday) : null
        });
        toast.add({ severity: 'success', summary: 'Created', detail: `${fullName} created.`, life: 3000 });
    }
    userDialog.value = false;
};

const deleteUserConfirmed = () => {
    users.value = users.value.filter((u) => u.id !== selectedUser.value.id);
    deleteDialog.value = false;
    selectedUser.value = null;
    toast.add({ severity: 'success', summary: 'Deleted', detail: 'User deleted.', life: 3000 });
};

const formatDate = (date) => {
    if (!date) return '';
    const d = new Date(date);
    return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
};
</script>

<template>
    <Toast />
    <div class="card">
        <div class="font-semibold text-xl mb-4">User Management</div>
        <DataTable :value="users" :paginator="true" :rows="10" dataKey="id" :rowHover="true" responsiveLayout="scroll">
            <template #header>
                <div class="flex justify-between items-center">
                    <span class="text-xl text-surface-900 dark:text-surface-0 font-bold">Users</span>
                    <Button label="Add User" icon="pi pi-plus" size="small" @click="openNew" />
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
            <Column header="Name" sortable style="min-width: 12rem">
                <template #body="{ data }">{{ data.firstName }} {{ data.lastName }}</template>
            </Column>
            <Column field="email" header="Email" sortable style="min-width: 14rem"></Column>
            <Column field="role" header="Role" sortable style="min-width: 8rem">
                <template #body="{ data }">
                    <Tag :value="data.role" :severity="getRoleSeverity(data.role)" />
                </template>
            </Column>
            <Column field="group" header="Group" sortable style="min-width: 8rem"></Column>
            <Column field="status" header="Status" sortable style="min-width: 8rem">
                <template #body="{ data }">
                    <Tag :value="data.status" :severity="data.status === 'Active' ? 'success' : 'secondary'" />
                </template>
            </Column>
            <Column field="lastLogin" header="Last Login" sortable style="min-width: 12rem"></Column>
            <Column header="Actions" style="min-width: 10rem">
                <template #body="{ data }">
                    <div class="flex gap-2">
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

                <div class="flex flex-col gap-2">
                    <label class="font-medium">Address</label>
                    <InputText v-model="user.address" placeholder="Search location..." />
                    <small class="text-muted-color"><i class="pi pi-map-marker mr-1"></i>Google Places integration — enter address manually for now</small>
                </div>

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
</template>
