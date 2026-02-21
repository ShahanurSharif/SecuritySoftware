<script setup>
import { ref, onMounted } from 'vue';
import { useToast } from 'primevue/usetoast';
import { QrcodeStream } from 'vue-qrcode-reader';
import api from '@/services/api';

const toast = useToast();

const scanning = ref(false);
const scanResult = ref(null);
const cameraError = ref('');
const loading = ref(false);

// Scan history from API
const scanHistory = ref([]);
const totalRecords = ref(0);
const currentPage = ref(1);
const rowsPerPage = ref(10);
const sortField = ref('scanned_at');
const sortOrder = ref(-1);
const historyLoading = ref(false);

// --- Filters ---
const users = ref([]);
const branches = ref([]);
const filterUser = ref(null);
const filterBranch = ref(null);
const filterArea = ref('');
const filterDateFrom = ref(null);
const filterDateTo = ref(null);

const fetchFilterOptions = async () => {
    try {
        const [uRes, bRes] = await Promise.all([api.get('/profiles/', { params: { page_size: 1000 } }), api.get('/branches/', { params: { page_size: 1000 } })]);
        users.value = (uRes.data.results || uRes.data).map((p) => ({
            label: `${p.first_name || ''} ${p.last_name || ''}`.trim() || `User ${p.id}`,
            value: p.id
        }));
        branches.value = (bRes.data.results || bRes.data).map((b) => ({
            label: b.name,
            value: b.id
        }));
    } catch {
        // silent
    }
};

const apiSortMap = {
    qr_area_name: 'qr_code__area_name',
    qr_branch_name: 'qr_code__branch__name',
    user_name: 'user__first_name',
    scanned_at: 'scanned_at'
};

const fetchHistory = async () => {
    historyLoading.value = true;
    try {
        const params = { page: currentPage.value, page_size: rowsPerPage.value };
        const key = apiSortMap[sortField.value] || sortField.value;
        params.ordering = (sortOrder.value === -1 ? '-' : '') + key;

        // Apply filters
        if (filterUser.value) params.scanned_by = filterUser.value;
        if (filterBranch.value) params.branch = filterBranch.value;
        if (filterArea.value.trim()) params.area = filterArea.value.trim();
        if (filterDateFrom.value) {
            const d = new Date(filterDateFrom.value);
            d.setHours(0, 0, 0, 0);
            params.scanned_after = d.toISOString();
        }
        if (filterDateTo.value) {
            const d = new Date(filterDateTo.value);
            d.setHours(23, 59, 59, 999);
            params.scanned_before = d.toISOString();
        }

        const { data } = await api.get('/qrcode-submissions/', { params });
        scanHistory.value = data.results;
        totalRecords.value = data.count;
    } catch {
        // silent
    } finally {
        historyLoading.value = false;
    }
};

const applyFilters = () => {
    currentPage.value = 1;
    fetchHistory();
};

const clearFilters = () => {
    filterUser.value = null;
    filterBranch.value = null;
    filterArea.value = '';
    filterDateFrom.value = null;
    filterDateTo.value = null;
    currentPage.value = 1;
    fetchHistory();
};

onMounted(() => {
    fetchFilterOptions();
    fetchHistory();
});

const onPage = (event) => {
    currentPage.value = Math.floor(event.first / event.rows) + 1;
    rowsPerPage.value = event.rows;
    fetchHistory();
};

const onSort = (event) => {
    sortField.value = event.sortField;
    sortOrder.value = event.sortOrder;
    currentPage.value = 1;
    fetchHistory();
};

const startScan = () => {
    scanning.value = true;
    scanResult.value = null;
    cameraError.value = '';
};

const stopScan = () => {
    scanning.value = false;
};

const onCameraError = (error) => {
    scanning.value = false;
    cameraError.value = error.message || 'Could not access camera.';
    toast.add({ severity: 'error', summary: 'Camera Error', detail: cameraError.value, life: 4000 });
};

const onDetect = async (detectedCodes) => {
    if (!detectedCodes || detectedCodes.length === 0) return;

    const raw = detectedCodes[0].rawValue;
    scanning.value = false;

    let parsed;
    try {
        parsed = JSON.parse(raw);
    } catch {
        toast.add({ severity: 'error', summary: 'Invalid QR', detail: 'This QR code is not recognized.', life: 4000 });
        return;
    }

    if (!parsed.qr_id) {
        toast.add({ severity: 'error', summary: 'Invalid QR', detail: 'QR code does not contain a valid ID.', life: 4000 });
        return;
    }

    // Submit scan to backend
    loading.value = true;
    try {
        const { data } = await api.post(`/qrcodes/${parsed.qr_id}/submit/`);
        scanResult.value = {
            area: parsed.area || data.qr_area_name,
            branch: parsed.branch || data.qr_branch_name,
            scannedAt: new Date(data.scanned_at).toLocaleString()
        };
        toast.add({ severity: 'success', summary: 'Scan Recorded', detail: `Scanned: ${scanResult.value.area}`, life: 3000 });
        fetchHistory();
    } catch (err) {
        const msg = err.response?.data?.detail || 'Failed to submit scan.';
        toast.add({ severity: 'error', summary: 'Error', detail: msg, life: 4000 });
    } finally {
        loading.value = false;
    }
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

                <div class="flex flex-col items-center gap-4">
                    <div class="w-full aspect-square bg-surface-100 dark:bg-surface-800 rounded-xl border-2 border-dashed border-surface-300 dark:border-surface-600 overflow-hidden flex flex-col items-center justify-center relative">
                        <!-- Live camera with QR detection -->
                        <QrcodeStream v-if="scanning" @detect="onDetect" @error="onCameraError" class="w-full h-full" />

                        <!-- Loading spinner after scan -->
                        <div v-else-if="loading" class="flex flex-col items-center gap-2">
                            <i class="pi pi-spin pi-spinner text-4xl text-primary"></i>
                            <span class="text-muted-color">Submitting scan...</span>
                        </div>

                        <!-- Scan result -->
                        <template v-else-if="scanResult">
                            <i class="pi pi-check-circle text-5xl text-green-500"></i>
                            <div class="text-center mt-2">
                                <div class="font-semibold text-lg">{{ scanResult.area }}</div>
                                <div class="text-muted-color text-sm mt-1">{{ scanResult.branch }}</div>
                                <div class="text-muted-color text-xs mt-1">{{ scanResult.scannedAt }}</div>
                            </div>
                        </template>

                        <!-- Placeholder -->
                        <template v-else>
                            <i class="pi pi-camera text-5xl text-surface-400"></i>
                            <span class="text-muted-color text-center px-4 mt-2">Position the QR code within the frame and tap Scan</span>
                        </template>
                    </div>

                    <div class="flex gap-2 w-full">
                        <Button v-if="!scanning" :label="scanResult ? 'Scan Again' : 'Start Scanning'" icon="pi pi-camera" @click="startScan" class="flex-1" :disabled="loading" />
                        <Button v-if="scanning" label="Stop" icon="pi pi-stop" severity="danger" @click="stopScan" class="flex-1" />
                        <Button v-if="scanResult" label="Clear" icon="pi pi-times" severity="secondary" outlined @click="clearResult" />
                    </div>
                </div>
            </div>
        </div>

        <!-- Scan History -->
        <div class="lg:col-span-2">
            <div class="card">
                <div class="font-semibold text-xl mb-4">Scan History</div>

                <!-- Filters -->
                <div class="grid grid-cols-1 md:grid-cols-3 gap-3 mb-4">
                    <Select v-model="filterUser" :options="users" optionLabel="label" optionValue="value" placeholder="Scanned By" showClear filter class="w-full" />
                    <Select v-model="filterBranch" :options="branches" optionLabel="label" optionValue="value" placeholder="Branch" showClear filter class="w-full" />
                    <InputText v-model="filterArea" placeholder="Area" class="w-full" />
                    <DatePicker v-model="filterDateFrom" placeholder="Date From" dateFormat="yy-mm-dd" showIcon class="w-full" />
                    <DatePicker v-model="filterDateTo" placeholder="Date To" dateFormat="yy-mm-dd" showIcon class="w-full" />
                    <div class="flex gap-2">
                        <Button label="Filter" icon="pi pi-filter" @click="applyFilters" class="flex-1" />
                        <Button label="Clear" icon="pi pi-filter-slash" severity="secondary" outlined @click="clearFilters" />
                    </div>
                </div>

                <DataTable
                    :value="scanHistory"
                    :paginator="true"
                    :rows="rowsPerPage"
                    :totalRecords="totalRecords"
                    :lazy="true"
                    :loading="historyLoading"
                    :rowsPerPageOptions="[10, 25, 50]"
                    @page="onPage"
                    @sort="onSort"
                    dataKey="id"
                    :rowHover="true"
                    responsiveLayout="scroll"
                >
                    <template #empty>No scans recorded yet.</template>
                    <Column field="qr_area_name" header="Area" sortable style="min-width: 12rem" />
                    <Column field="qr_branch_name" header="Branch" sortable style="min-width: 12rem" />
                    <Column field="user_name" header="Scanned By" sortable style="min-width: 10rem" />
                    <Column field="scanned_at" header="Time" sortable style="min-width: 14rem">
                        <template #body="{ data }">
                            {{ new Date(data.scanned_at).toLocaleString() }}
                        </template>
                    </Column>
                </DataTable>
            </div>
        </div>
    </div>
</template>
