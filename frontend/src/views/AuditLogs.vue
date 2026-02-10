<script setup>
import { ref } from 'vue';

const logs = ref([
    { id: 1, user: 'admin@security.io', action: 'Login', resource: 'Auth System', ip: '192.168.1.10', timestamp: '2026-02-10 08:00:00', status: 'Success' },
    { id: 2, user: 'john.doe@security.io', action: 'Update', resource: 'Firewall Rules', ip: '10.0.0.5', timestamp: '2026-02-10 07:45:00', status: 'Success' },
    { id: 3, user: 'unknown', action: 'Login', resource: 'Auth System', ip: '203.0.113.50', timestamp: '2026-02-10 07:30:00', status: 'Failed' },
    { id: 4, user: 'admin@security.io', action: 'Delete', resource: 'User Account', ip: '192.168.1.10', timestamp: '2026-02-09 18:20:00', status: 'Success' },
    { id: 5, user: 'jane.smith@security.io', action: 'Export', resource: 'Audit Logs', ip: '10.0.0.8', timestamp: '2026-02-09 16:00:00', status: 'Success' },
    { id: 6, user: 'unknown', action: 'Login', resource: 'Auth System', ip: '198.51.100.23', timestamp: '2026-02-09 14:10:00', status: 'Failed' }
]);

const getStatusSeverity = (status) => {
    return status === 'Success' ? 'success' : 'danger';
};
</script>

<template>
    <div class="card">
        <div class="font-semibold text-xl mb-4">Audit Logs</div>
        <DataTable :value="logs" :paginator="true" :rows="10" dataKey="id" :rowHover="true" responsiveLayout="scroll">
            <template #header>
                <div class="flex justify-between items-center">
                    <span class="text-xl text-surface-900 dark:text-surface-0 font-bold">Activity Log</span>
                    <div class="flex gap-2">
                        <Button label="Export" icon="pi pi-download" outlined size="small" />
                        <Button icon="pi pi-refresh" rounded outlined />
                    </div>
                </div>
            </template>
            <template #empty> No logs found. </template>
            <Column field="timestamp" header="Timestamp" sortable style="min-width: 12rem"></Column>
            <Column field="user" header="User" sortable style="min-width: 14rem"></Column>
            <Column field="action" header="Action" sortable style="min-width: 8rem">
                <template #body="{ data }">
                    <Tag :value="data.action" severity="info" />
                </template>
            </Column>
            <Column field="resource" header="Resource" sortable style="min-width: 12rem"></Column>
            <Column field="ip" header="IP Address" sortable style="min-width: 10rem">
                <template #body="{ data }">
                    <span class="font-mono text-sm">{{ data.ip }}</span>
                </template>
            </Column>
            <Column field="status" header="Status" sortable style="min-width: 8rem">
                <template #body="{ data }">
                    <Tag :value="data.status" :severity="getStatusSeverity(data.status)" />
                </template>
            </Column>
        </DataTable>
    </div>
</template>
