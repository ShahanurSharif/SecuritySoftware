<script setup>
import { ref } from 'vue';

const threats = ref([
    { id: 1, name: 'Trojan.GenericKD', type: 'Malware', severity: 'Critical', source: '192.168.1.45', status: 'Active', detectedAt: '2026-02-10 08:23:00' },
    { id: 2, name: 'CVE-2025-1234', type: 'Vulnerability', severity: 'High', source: '10.0.0.22', status: 'Investigating', detectedAt: '2026-02-10 07:15:00' },
    { id: 3, name: 'SQL Injection Attempt', type: 'Attack', severity: 'High', source: '203.0.113.50', status: 'Blocked', detectedAt: '2026-02-09 22:45:00' },
    { id: 4, name: 'Phishing Campaign', type: 'Social Engineering', severity: 'Medium', source: 'email-gateway', status: 'Mitigated', detectedAt: '2026-02-09 18:30:00' },
    { id: 5, name: 'DDoS Attack Pattern', type: 'Attack', severity: 'Critical', source: 'Multiple IPs', status: 'Blocked', detectedAt: '2026-02-09 14:12:00' }
]);

const filters = ref({});
const severityOptions = ['Critical', 'High', 'Medium', 'Low'];
const statusOptions = ['Active', 'Investigating', 'Blocked', 'Mitigated', 'Resolved'];

const getSeverity = (severity) => {
    const map = { Critical: 'danger', High: 'warn', Medium: 'info', Low: 'success' };
    return map[severity] || 'info';
};

const getStatusSeverity = (status) => {
    const map = { Active: 'danger', Investigating: 'warn', Blocked: 'success', Mitigated: 'info', Resolved: 'secondary' };
    return map[status] || 'info';
};
</script>

<template>
    <div class="card">
        <div class="font-semibold text-xl mb-4">Threat Management</div>
        <DataTable :value="threats" :paginator="true" :rows="10" dataKey="id" :rowHover="true" filterDisplay="menu" :filters="filters"
            showGridlines responsiveLayout="scroll">
            <template #header>
                <div class="flex justify-between items-center">
                    <span class="text-xl text-surface-900 dark:text-surface-0 font-bold">Active Threats</span>
                    <Button icon="pi pi-refresh" rounded outlined />
                </div>
            </template>
            <template #empty> No threats found. </template>
            <Column field="name" header="Threat Name" sortable style="min-width: 14rem"></Column>
            <Column field="type" header="Type" sortable style="min-width: 10rem"></Column>
            <Column field="severity" header="Severity" sortable style="min-width: 10rem">
                <template #body="{ data }">
                    <Tag :value="data.severity" :severity="getSeverity(data.severity)" />
                </template>
            </Column>
            <Column field="source" header="Source" sortable style="min-width: 12rem">
                <template #body="{ data }">
                    <span class="font-mono text-sm">{{ data.source }}</span>
                </template>
            </Column>
            <Column field="status" header="Status" sortable style="min-width: 10rem">
                <template #body="{ data }">
                    <Tag :value="data.status" :severity="getStatusSeverity(data.status)" />
                </template>
            </Column>
            <Column field="detectedAt" header="Detected" sortable style="min-width: 12rem"></Column>
            <Column header="Actions" style="min-width: 8rem">
                <template #body>
                    <div class="flex gap-2">
                        <Button icon="pi pi-eye" rounded outlined severity="info" size="small" />
                        <Button icon="pi pi-shield" rounded outlined severity="warn" size="small" />
                    </div>
                </template>
            </Column>
        </DataTable>
    </div>
</template>
