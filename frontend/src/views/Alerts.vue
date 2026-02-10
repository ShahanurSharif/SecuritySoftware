<script setup>
import { ref } from 'vue';

const alerts = ref([
    { id: 1, type: 'Critical', message: 'Unauthorized access attempt detected on port 22', source: '192.168.1.45', timestamp: '2026-02-10 08:23:00', acknowledged: false },
    { id: 2, type: 'Warning', message: 'Unusual outbound traffic detected', source: '10.0.0.12', timestamp: '2026-02-10 07:15:00', acknowledged: false },
    { id: 3, type: 'Info', message: 'Firewall rule updated successfully', source: 'System', timestamp: '2026-02-10 06:00:00', acknowledged: true },
    { id: 4, type: 'Critical', message: 'Malware signature detected in uploaded file', source: '172.16.0.89', timestamp: '2026-02-09 22:45:00', acknowledged: false },
    { id: 5, type: 'Warning', message: 'SSL certificate expires in 7 days', source: 'api.example.com', timestamp: '2026-02-09 18:30:00', acknowledged: true },
    { id: 6, type: 'Info', message: 'System backup completed', source: 'System', timestamp: '2026-02-09 15:00:00', acknowledged: true }
]);

const getSeverity = (type) => {
    const map = { Critical: 'danger', Warning: 'warn', Info: 'info' };
    return map[type] || 'info';
};
</script>

<template>
    <div class="card">
        <div class="font-semibold text-xl mb-4">Alerts</div>
        <DataTable :value="alerts" :paginator="true" :rows="10" dataKey="id" :rowHover="true" responsiveLayout="scroll">
            <template #header>
                <div class="flex justify-between items-center">
                    <span class="text-xl text-surface-900 dark:text-surface-0 font-bold">Security Alerts</span>
                    <div class="flex gap-2">
                        <Button label="Mark All Read" icon="pi pi-check" outlined size="small" />
                        <Button icon="pi pi-refresh" rounded outlined />
                    </div>
                </div>
            </template>
            <template #empty> No alerts found. </template>
            <Column field="type" header="Severity" sortable style="min-width: 8rem">
                <template #body="{ data }">
                    <Tag :value="data.type" :severity="getSeverity(data.type)" />
                </template>
            </Column>
            <Column field="message" header="Message" sortable style="min-width: 20rem"></Column>
            <Column field="source" header="Source" sortable style="min-width: 12rem">
                <template #body="{ data }">
                    <span class="font-mono text-sm">{{ data.source }}</span>
                </template>
            </Column>
            <Column field="timestamp" header="Time" sortable style="min-width: 12rem"></Column>
            <Column field="acknowledged" header="Status" style="min-width: 8rem">
                <template #body="{ data }">
                    <Tag :value="data.acknowledged ? 'Acknowledged' : 'New'" :severity="data.acknowledged ? 'secondary' : 'warn'" />
                </template>
            </Column>
            <Column header="Actions" style="min-width: 8rem">
                <template #body>
                    <div class="flex gap-2">
                        <Button icon="pi pi-eye" rounded outlined severity="info" size="small" />
                        <Button icon="pi pi-check" rounded outlined severity="success" size="small" />
                    </div>
                </template>
            </Column>
        </DataTable>
    </div>
</template>
