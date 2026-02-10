<script setup>
import { ref } from 'vue';

const users = ref([
    { id: 1, name: 'Admin User', email: 'admin@security.io', role: 'Admin', status: 'Active', lastLogin: '2026-02-10 08:00:00' },
    { id: 2, name: 'John Doe', email: 'john.doe@security.io', role: 'Analyst', status: 'Active', lastLogin: '2026-02-10 07:45:00' },
    { id: 3, name: 'Jane Smith', email: 'jane.smith@security.io', role: 'Analyst', status: 'Active', lastLogin: '2026-02-09 16:00:00' },
    { id: 4, name: 'Bob Wilson', email: 'bob.wilson@security.io', role: 'Viewer', status: 'Inactive', lastLogin: '2026-01-15 10:30:00' }
]);

const getRoleSeverity = (role) => {
    const map = { Admin: 'danger', Analyst: 'info', Viewer: 'secondary' };
    return map[role] || 'secondary';
};
</script>

<template>
    <div class="card">
        <div class="font-semibold text-xl mb-4">User Management</div>
        <DataTable :value="users" :paginator="true" :rows="10" dataKey="id" :rowHover="true" responsiveLayout="scroll">
            <template #header>
                <div class="flex justify-between items-center">
                    <span class="text-xl text-surface-900 dark:text-surface-0 font-bold">Users</span>
                    <Button label="Add User" icon="pi pi-plus" size="small" />
                </div>
            </template>
            <template #empty> No users found. </template>
            <Column field="name" header="Name" sortable style="min-width: 12rem"></Column>
            <Column field="email" header="Email" sortable style="min-width: 14rem"></Column>
            <Column field="role" header="Role" sortable style="min-width: 8rem">
                <template #body="{ data }">
                    <Tag :value="data.role" :severity="getRoleSeverity(data.role)" />
                </template>
            </Column>
            <Column field="status" header="Status" sortable style="min-width: 8rem">
                <template #body="{ data }">
                    <Tag :value="data.status" :severity="data.status === 'Active' ? 'success' : 'secondary'" />
                </template>
            </Column>
            <Column field="lastLogin" header="Last Login" sortable style="min-width: 12rem"></Column>
            <Column header="Actions" style="min-width: 10rem">
                <template #body>
                    <div class="flex gap-2">
                        <Button icon="pi pi-pencil" rounded outlined severity="info" size="small" />
                        <Button icon="pi pi-trash" rounded outlined severity="danger" size="small" />
                    </div>
                </template>
            </Column>
        </DataTable>
    </div>
</template>
