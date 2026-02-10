<script setup>
import { ref } from 'vue';

const stats = ref([
    { label: 'Threats Detected', value: '24', icon: 'pi pi-shield', severity: 'danger', change: '+12%' },
    { label: 'Active Alerts', value: '8', icon: 'pi pi-bell', severity: 'warn', change: '+5%' },
    { label: 'Systems Monitored', value: '156', icon: 'pi pi-server', severity: 'info', change: '+3%' },
    { label: 'Blocked Attacks', value: '1,204', icon: 'pi pi-ban', severity: 'success', change: '+18%' }
]);

const recentAlerts = ref([
    { id: 1, type: 'Critical', message: 'Unauthorized access attempt detected', source: '192.168.1.45', time: '2 min ago', severity: 'danger' },
    { id: 2, type: 'Warning', message: 'Unusual outbound traffic pattern', source: '10.0.0.12', time: '15 min ago', severity: 'warn' },
    { id: 3, type: 'Info', message: 'Firewall rule updated successfully', source: 'System', time: '1 hour ago', severity: 'info' },
    { id: 4, type: 'Critical', message: 'Malware signature detected in upload', source: '172.16.0.89', time: '2 hours ago', severity: 'danger' },
    { id: 5, type: 'Warning', message: 'SSL certificate expiring in 7 days', source: 'api.example.com', time: '3 hours ago', severity: 'warn' }
]);

const threatTypes = ref([
    { type: 'Malware', count: 12, percentage: 35 },
    { type: 'Phishing', count: 8, percentage: 24 },
    { type: 'DDoS', count: 6, percentage: 18 },
    { type: 'Brute Force', count: 5, percentage: 15 },
    { type: 'Other', count: 3, percentage: 8 }
]);
</script>

<template>
    <div class="grid grid-cols-12 gap-8">
        <!-- Stats Cards -->
        <div v-for="stat in stats" :key="stat.label" class="col-span-12 lg:col-span-6 xl:col-span-3">
            <div class="card mb-0">
                <div class="flex justify-between mb-4">
                    <div>
                        <span class="block text-muted-color font-medium mb-4">{{ stat.label }}</span>
                        <div class="text-surface-900 dark:text-surface-0 font-medium text-xl">{{ stat.value }}</div>
                    </div>
                    <div class="flex items-center justify-center bg-primary/10 rounded-border" style="width: 2.5rem; height: 2.5rem">
                        <i :class="[stat.icon, 'text-primary text-xl']"></i>
                    </div>
                </div>
                <span class="text-primary font-medium">{{ stat.change }} </span>
                <span class="text-muted-color">since last week</span>
            </div>
        </div>

        <!-- Recent Alerts -->
        <div class="col-span-12 xl:col-span-7">
            <div class="card">
                <div class="font-semibold text-xl mb-4">Recent Alerts</div>
                <DataTable :value="recentAlerts" :rows="5" responsiveLayout="scroll">
                    <Column field="type" header="Type" style="width: 15%">
                        <template #body="slotProps">
                            <Tag :value="slotProps.data.type" :severity="slotProps.data.severity" />
                        </template>
                    </Column>
                    <Column field="message" header="Message" style="width: 40%"></Column>
                    <Column field="source" header="Source" style="width: 20%">
                        <template #body="slotProps">
                            <span class="font-mono text-sm">{{ slotProps.data.source }}</span>
                        </template>
                    </Column>
                    <Column field="time" header="Time" style="width: 25%"></Column>
                </DataTable>
            </div>
        </div>

        <!-- Threat Distribution -->
        <div class="col-span-12 xl:col-span-5">
            <div class="card">
                <div class="font-semibold text-xl mb-4">Threat Distribution</div>
                <ul class="list-none p-0 m-0">
                    <li v-for="threat in threatTypes" :key="threat.type" class="flex flex-col gap-2 mb-6">
                        <div class="flex items-center justify-between">
                            <span class="text-surface-900 dark:text-surface-0 font-medium">{{ threat.type }}</span>
                            <span class="text-muted-color font-medium">{{ threat.count }} incidents ({{ threat.percentage }}%)</span>
                        </div>
                        <ProgressBar :value="threat.percentage" :showValue="false" style="height: 0.5rem" />
                    </li>
                </ul>
            </div>
        </div>

        <!-- System Status -->
        <div class="col-span-12">
            <div class="card">
                <div class="font-semibold text-xl mb-4">System Status</div>
                <div class="grid grid-cols-12 gap-4">
                    <div class="col-span-12 md:col-span-4">
                        <div class="flex items-center gap-2 p-4 rounded-border bg-green-50 dark:bg-green-400/10">
                            <i class="pi pi-check-circle text-green-500 text-2xl"></i>
                            <div>
                                <div class="text-surface-900 dark:text-surface-0 font-medium">Firewall</div>
                                <span class="text-green-600 dark:text-green-400 text-sm">Active & Running</span>
                            </div>
                        </div>
                    </div>
                    <div class="col-span-12 md:col-span-4">
                        <div class="flex items-center gap-2 p-4 rounded-border bg-green-50 dark:bg-green-400/10">
                            <i class="pi pi-check-circle text-green-500 text-2xl"></i>
                            <div>
                                <div class="text-surface-900 dark:text-surface-0 font-medium">Intrusion Detection</div>
                                <span class="text-green-600 dark:text-green-400 text-sm">Active & Running</span>
                            </div>
                        </div>
                    </div>
                    <div class="col-span-12 md:col-span-4">
                        <div class="flex items-center gap-2 p-4 rounded-border bg-orange-50 dark:bg-orange-400/10">
                            <i class="pi pi-exclamation-triangle text-orange-500 text-2xl"></i>
                            <div>
                                <div class="text-surface-900 dark:text-surface-0 font-medium">Antivirus</div>
                                <span class="text-orange-600 dark:text-orange-400 text-sm">Update Available</span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</template>
