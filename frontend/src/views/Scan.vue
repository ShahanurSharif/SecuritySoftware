<script setup>
import { ref } from 'vue';
import { useToast } from 'primevue/usetoast';

const toast = useToast();

const scanResult = ref(null);
const scanning = ref(false);
const scanHistory = ref([
    { id: 1, qrName: 'Main Entrance', location: 'Building A — Front Door', scannedBy: 'John Doe', scannedAt: '2026-02-10 08:15:00', status: 'Completed' },
    { id: 2, qrName: 'Parking Level 1', location: 'Building A — Basement P1', scannedBy: 'Jane Smith', scannedAt: '2026-02-10 08:30:00', status: 'Completed' },
    { id: 3, qrName: 'Server Room', location: 'Building B — Floor 3', scannedBy: 'John Doe', scannedAt: '2026-02-10 09:00:00', status: 'Completed' }
]);

let nextScanId = 4;

const startScan = () => {
    scanning.value = true;
    scanResult.value = null;

    // TODO: Replace with real camera / QR scanner integration
    setTimeout(() => {
        scanning.value = false;
        scanResult.value = {
            qrName: 'Main Entrance',
            location: 'Building A — Front Door',
            timestamp: new Date().toISOString().replace('T', ' ').slice(0, 19)
        };

        scanHistory.value.unshift({
            id: nextScanId++,
            qrName: scanResult.value.qrName,
            location: scanResult.value.location,
            scannedBy: 'Current User',
            scannedAt: scanResult.value.timestamp,
            status: 'Completed'
        });

        toast.add({ severity: 'success', summary: 'Scan Complete', detail: `Scanned: ${scanResult.value.qrName}`, life: 3000 });
    }, 2000);
};

const clearResult = () => {
    scanResult.value = null;
};
</script>

<template>
    <Toast />
    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <!-- Scanner Panel -->
        <div class="lg:col-span-1">
            <div class="card">
                <div class="font-semibold text-xl mb-4">QR Scanner</div>

                <!-- Camera Viewfinder Area -->
                <div class="flex flex-col items-center gap-4">
                    <div class="w-full aspect-square bg-surface-100 dark:bg-surface-800 rounded-xl border-2 border-dashed border-surface-300 dark:border-surface-600 flex flex-col items-center justify-center gap-4">
                        <template v-if="scanning">
                            <i class="pi pi-spin pi-spinner text-4xl text-primary"></i>
                            <span class="text-muted-color">Scanning...</span>
                        </template>
                        <template v-else-if="scanResult">
                            <i class="pi pi-check-circle text-5xl text-green-500"></i>
                            <div class="text-center">
                                <div class="font-semibold text-lg">{{ scanResult.qrName }}</div>
                                <div class="text-muted-color text-sm mt-1">{{ scanResult.location }}</div>
                                <div class="text-muted-color text-xs mt-1">{{ scanResult.timestamp }}</div>
                            </div>
                        </template>
                        <template v-else>
                            <i class="pi pi-camera text-5xl text-surface-400"></i>
                            <span class="text-muted-color text-center px-4">Position the QR code within the frame and tap Scan</span>
                        </template>
                    </div>

                    <div class="flex gap-2 w-full">
                        <Button :label="scanning ? 'Scanning...' : 'Scan QR Code'" icon="pi pi-camera" @click="startScan" :disabled="scanning" class="flex-1" />
                        <Button v-if="scanResult" label="Clear" icon="pi pi-times" severity="secondary" outlined @click="clearResult" />
                    </div>

                    <small class="text-muted-color text-center">
                        <i class="pi pi-info-circle mr-1"></i>Camera-based QR scanning will be integrated with the backend.
                    </small>
                </div>
            </div>
        </div>

        <!-- Scan History -->
        <div class="lg:col-span-2">
            <div class="card">
                <div class="font-semibold text-xl mb-4">Scan History</div>
                <DataTable :value="scanHistory" :paginator="true" :rows="10" dataKey="id" :rowHover="true" responsiveLayout="scroll">
                    <template #empty> No scans recorded yet. </template>
                    <Column field="qrName" header="QR Code" sortable style="min-width: 12rem"></Column>
                    <Column field="location" header="Location" sortable style="min-width: 14rem"></Column>
                    <Column field="scannedBy" header="Scanned By" sortable style="min-width: 10rem"></Column>
                    <Column field="scannedAt" header="Time" sortable style="min-width: 12rem"></Column>
                    <Column field="status" header="Status" sortable style="min-width: 8rem">
                        <template #body="{ data }">
                            <Tag :value="data.status" severity="success" />
                        </template>
                    </Column>
                </DataTable>
            </div>
        </div>
    </div>
</template>
