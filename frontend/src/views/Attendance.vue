<script setup>
import { ref, onMounted, onBeforeUnmount } from 'vue';
import { useToast } from 'primevue/usetoast';
import api from '@/services/api';

const toast = useToast();

// --- State ---
const isClockedIn = ref(false);
const nextType = ref('clock_in');
const cameraActive = ref(false);
const videoRef = ref(null);
const canvasRef = ref(null);
const capturedImage = ref(null);
const capturedFile = ref(null);
const ocrTime = ref('');
const ocrBranch = ref('');
const ocrProcessing = ref(false);
const submitting = ref(false);
const stream = ref(null);

// Manual request
const manualRequestDialog = ref(false);
const manualSubmitted = ref(false);
const branches = ref([]);
const manualRequest = ref({
    type: 'clock_in',
    branch: null,
    date: null,
    time: '',
    reason: ''
});

// Attendance records (lazy DataTable)
const records = ref([]);
const totalRecords = ref(0);
const currentPage = ref(1);
const rowsPerPage = ref(10);
const sortField = ref('created_at');
const sortOrder = ref(-1);
const tableLoading = ref(false);

// Filters
const users = ref([]);
const filterUser = ref(null);
const filterType = ref(null);
const filterBranch = ref(null);
const filterDateFrom = ref(null);
const filterDateTo = ref(null);

// Image preview
const previewImage = ref(null);
const previewDialog = ref(false);

const typeOptions = [
    { label: 'Clock In', value: 'clock_in' },
    { label: 'Clock Out', value: 'clock_out' }
];

const apiSortMap = {
    user_name: 'user__first_name',
    branch_name: 'branch__name',
    created_at: 'created_at',
    type: 'type',
    method: 'method',
    status: 'status'
};

// --- Fetch helpers ---
const fetchClockStatus = async () => {
    try {
        const { data } = await api.get('/attendance/clock-status/');
        isClockedIn.value = data.is_clocked_in;
        nextType.value = data.next_type;
    } catch {
        // default
    }
};

const fetchRecords = async () => {
    tableLoading.value = true;
    try {
        const params = { page: currentPage.value, page_size: rowsPerPage.value };
        const key = apiSortMap[sortField.value] || sortField.value;
        params.ordering = (sortOrder.value === -1 ? '-' : '') + key;

        // Apply filters
        if (filterUser.value) params.scanned_by = filterUser.value;
        if (filterType.value) params.type = filterType.value;
        if (filterBranch.value) params.branch = filterBranch.value;
        if (filterDateFrom.value) {
            const d = new Date(filterDateFrom.value);
            d.setHours(0, 0, 0, 0);
            params.date_from = d.toISOString();
        }
        if (filterDateTo.value) {
            const d = new Date(filterDateTo.value);
            d.setHours(23, 59, 59, 999);
            params.date_to = d.toISOString();
        }

        const { data } = await api.get('/attendance/', { params });
        records.value = data.results;
        totalRecords.value = data.count;
    } catch {
        // silent
    } finally {
        tableLoading.value = false;
    }
};

const fetchBranches = async () => {
    try {
        const { data } = await api.get('/branches/', { params: { page_size: 1000 } });
        branches.value = (data.results || data).map((b) => ({ label: b.name, value: b.id }));
    } catch {
        // silent
    }
};

const fetchUsers = async () => {
    try {
        const { data } = await api.get('/profiles/', { params: { page_size: 1000 } });
        users.value = (data.results || data).map((p) => ({
            label: `${p.first_name || ''} ${p.last_name || ''}`.trim() || `User ${p.id}`,
            value: p.id
        }));
    } catch {
        // silent
    }
};

let filterTimeout = null;
const onFilterChange = () => {
    clearTimeout(filterTimeout);
    filterTimeout = setTimeout(() => {
        currentPage.value = 1;
        fetchRecords();
    }, 400);
};

const clearFilters = () => {
    filterUser.value = null;
    filterType.value = null;
    filterBranch.value = null;
    filterDateFrom.value = null;
    filterDateTo.value = null;
    currentPage.value = 1;
    fetchRecords();
};

const openImagePreview = (url) => {
    previewImage.value = url;
    previewDialog.value = true;
};

onMounted(() => {
    fetchClockStatus();
    fetchRecords();
    fetchBranches();
    fetchUsers();
});

const onPage = (event) => {
    currentPage.value = Math.floor(event.first / event.rows) + 1;
    rowsPerPage.value = event.rows;
    fetchRecords();
};

const onSort = (event) => {
    sortField.value = event.sortField;
    sortOrder.value = event.sortOrder;
    currentPage.value = 1;
    fetchRecords();
};

// --- Camera ---
const startCamera = async () => {
    try {
        const mediaStream = await navigator.mediaDevices.getUserMedia({
            video: { facingMode: 'environment', width: { ideal: 640 }, height: { ideal: 480 } }
        });
        stream.value = mediaStream;
        cameraActive.value = true;
        capturedImage.value = null;
        capturedFile.value = null;
        ocrTime.value = '';
        ocrBranch.value = '';

        await new Promise((r) => setTimeout(r, 100));
        if (videoRef.value) {
            videoRef.value.srcObject = mediaStream;
            videoRef.value.play();
        }
    } catch {
        toast.add({ severity: 'error', summary: 'Camera Error', detail: 'Could not access camera. Please grant permission.', life: 4000 });
    }
};

const stopCamera = () => {
    if (stream.value) {
        stream.value.getTracks().forEach((t) => t.stop());
        stream.value = null;
    }
    cameraActive.value = false;
};

const capturePhoto = () => {
    if (!videoRef.value || !canvasRef.value) return;

    const video = videoRef.value;
    const canvas = canvasRef.value;
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    const ctx = canvas.getContext('2d');
    ctx.drawImage(video, 0, 0);

    capturedImage.value = canvas.toDataURL('image/png');
    // Convert to File for upload
    canvas.toBlob((blob) => {
        capturedFile.value = new File([blob], 'attendance.png', { type: 'image/png' });
        stopCamera();
        runOCR();
    }, 'image/png');
};

const runOCR = async () => {
    if (!capturedFile.value) return;
    ocrProcessing.value = true;

    try {
        const form = new FormData();
        form.append('image', capturedFile.value);
        const { data } = await api.post('/attendance/ocr/', form, {
            headers: { 'Content-Type': 'multipart/form-data' }
        });
        ocrTime.value = data.time || '';
        ocrBranch.value = data.branch_name || '';

        if (ocrTime.value) {
            toast.add({ severity: 'info', summary: 'OCR Complete', detail: `Time: ${ocrTime.value}${ocrBranch.value ? ', Branch: ' + ocrBranch.value : ''}`, life: 4000 });
        } else {
            toast.add({ severity: 'warn', summary: 'OCR', detail: 'Could not detect time from the photo. You can still submit or retake.', life: 4000 });
        }
    } catch {
        toast.add({ severity: 'error', summary: 'OCR Failed', detail: 'Could not process image. You can still submit or retake.', life: 4000 });
    } finally {
        ocrProcessing.value = false;
    }
};

const retakePhoto = () => {
    capturedImage.value = null;
    capturedFile.value = null;
    ocrTime.value = '';
    ocrBranch.value = '';
    startCamera();
};

// --- Submit attendance (camera) ---
const submitAttendance = async () => {
    submitting.value = true;
    try {
        const form = new FormData();
        form.append('captured_time', ocrTime.value);
        form.append('captured_branch', ocrBranch.value);
        if (capturedFile.value) form.append('image', capturedFile.value);

        const { data } = await api.post('/attendance/submit/', form, {
            headers: { 'Content-Type': 'multipart/form-data' }
        });

        const typeLabel = data.type === 'clock_in' ? 'Clock In' : 'Clock Out';
        toast.add({ severity: 'success', summary: typeLabel, detail: `${typeLabel} recorded successfully.`, life: 3000 });

        capturedImage.value = null;
        capturedFile.value = null;
        ocrTime.value = '';
        ocrBranch.value = '';

        await fetchClockStatus();
        await fetchRecords();
    } catch (err) {
        const msg = err.response?.data?.detail || 'Failed to submit attendance.';
        toast.add({ severity: 'error', summary: 'Error', detail: msg, life: 4000 });
    } finally {
        submitting.value = false;
    }
};

// --- Manual Request ---
const openManualRequest = () => {
    manualRequest.value = { type: nextType.value, branch: null, date: null, time: '', reason: '' };
    manualSubmitted.value = false;
    manualRequestDialog.value = true;
};

const submitManualRequest = async () => {
    manualSubmitted.value = true;
    if (!manualRequest.value.date || !manualRequest.value.time.trim() || !manualRequest.value.reason.trim()) return;

    try {
        await api.post('/attendance/manual/', {
            type: manualRequest.value.type,
            branch: manualRequest.value.branch,
            captured_time: manualRequest.value.time,
            reason: manualRequest.value.reason,
        });

        manualRequestDialog.value = false;
        toast.add({ severity: 'warn', summary: 'Manual Request Sent', detail: 'Your manual attendance request has been sent to the admin for approval.', life: 4000 });
        await fetchRecords();
    } catch (err) {
        const msg = err.response?.data?.detail || 'Failed to submit manual request.';
        toast.add({ severity: 'error', summary: 'Error', detail: msg, life: 4000 });
    }
};

const getTypeSeverity = (type) => (type === 'clock_in' ? 'success' : 'info');
const getStatusSeverity = (s) => {
    if (s === 'approved') return 'success';
    if (s === 'pending') return 'warn';
    return 'danger';
};
const getMethodIcon = (m) => (m === 'camera' ? 'pi pi-camera' : 'pi pi-pencil');

onBeforeUnmount(() => {
    stopCamera();
});
</script>

<template>
    <Toast />
    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <!-- Clock In/Out Panel -->
        <div class="lg:col-span-1">
            <div class="card">
                <div class="font-semibold text-xl mb-4">Attendance</div>

                <!-- Current status badge -->
                <div class="flex items-center gap-2 mb-4">
                    <Tag :value="isClockedIn ? 'Clocked In' : 'Not Clocked In'" :severity="isClockedIn ? 'success' : 'secondary'" />
                    <span class="text-sm text-muted-color">{{ new Date().toLocaleDateString('en-AU', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' }) }}</span>
                </div>

                <!-- Camera / Capture Area -->
                <div class="flex flex-col items-center gap-4">
                    <div class="w-full aspect-[4/3] bg-surface-100 dark:bg-surface-800 rounded-xl border-2 border-dashed border-surface-300 dark:border-surface-600 overflow-hidden flex items-center justify-center relative">
                        <!-- Live camera feed -->
                        <video v-if="cameraActive" ref="videoRef" autoplay playsinline muted class="w-full h-full object-cover" />

                        <!-- Captured image preview -->
                        <div v-else-if="capturedImage" class="w-full h-full relative">
                            <img :src="capturedImage" alt="Captured" class="w-full h-full object-cover" />
                            <!-- OCR overlay -->
                            <div v-if="ocrProcessing" class="absolute inset-0 bg-black/50 flex flex-col items-center justify-center">
                                <i class="pi pi-spin pi-spinner text-3xl text-white mb-2"></i>
                                <span class="text-white text-sm">Extracting time &amp; branch...</span>
                            </div>
                            <div v-else-if="ocrTime || ocrBranch" class="absolute bottom-0 left-0 right-0 bg-black/60 p-2 text-center">
                                <div v-if="ocrTime">
                                    <span class="text-white text-sm">Time: </span>
                                    <span class="text-white font-bold text-lg">{{ ocrTime }}</span>
                                </div>
                                <div v-if="ocrBranch">
                                    <span class="text-white text-sm">Branch: </span>
                                    <span class="text-white font-bold">{{ ocrBranch }}</span>
                                </div>
                            </div>
                        </div>

                        <!-- Placeholder -->
                        <div v-else class="flex flex-col items-center gap-2 p-4">
                            <i class="pi pi-camera text-5xl text-surface-400"></i>
                            <span class="text-muted-color text-center text-sm">Open camera to capture your attendance photo</span>
                        </div>
                    </div>

                    <canvas ref="canvasRef" class="hidden" />

                    <!-- Action buttons -->
                    <div class="flex flex-col gap-2 w-full">
                        <div v-if="!cameraActive && !capturedImage" class="flex gap-2">
                            <Button :label="isClockedIn ? 'Clock Out' : 'Clock In'" :icon="isClockedIn ? 'pi pi-sign-out' : 'pi pi-sign-in'" @click="startCamera" class="flex-1" :severity="isClockedIn ? 'warn' : 'success'" />
                        </div>

                        <div v-if="cameraActive" class="flex gap-2">
                            <Button label="Capture" icon="pi pi-camera" @click="capturePhoto" class="flex-1" />
                            <Button label="Cancel" icon="pi pi-times" severity="secondary" outlined @click="stopCamera" />
                        </div>

                        <div v-if="capturedImage && !ocrProcessing" class="flex gap-2">
                            <Button :label="isClockedIn ? 'Confirm Clock Out' : 'Confirm Clock In'" :icon="isClockedIn ? 'pi pi-sign-out' : 'pi pi-check'" @click="submitAttendance" class="flex-1" :severity="isClockedIn ? 'warn' : 'success'" :loading="submitting" />
                            <Button label="Retake" icon="pi pi-refresh" severity="secondary" outlined @click="retakePhoto" :disabled="submitting" />
                        </div>
                    </div>

                    <Divider />

                    <!-- Manual request link -->
                    <div class="w-full text-center">
                        <small class="text-muted-color">Time inaccurate?</small>
                        <Button label="Request Manual Entry" icon="pi pi-pencil" severity="secondary" text size="small" @click="openManualRequest" class="mt-1" />
                    </div>
                </div>
            </div>
        </div>

        <!-- Attendance List -->
        <div class="lg:col-span-2">
            <div class="card">
                <div class="font-semibold text-xl mb-4">Attendance Records</div>

                <!-- Filters -->
                <div class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3 mb-4">
                    <Select v-model="filterUser" :options="users" optionLabel="label" optionValue="value" placeholder="User" showClear filter class="w-full" @change="onFilterChange" />
                    <Select v-model="filterType" :options="typeOptions" optionLabel="label" optionValue="value" placeholder="Type" showClear class="w-full" @change="onFilterChange" />
                    <Select v-model="filterBranch" :options="branches" optionLabel="label" optionValue="value" placeholder="Branch" showClear filter class="w-full" @change="onFilterChange" />
                    <DatePicker v-model="filterDateFrom" placeholder="Date From" dateFormat="yy-mm-dd" showIcon class="w-full" @date-select="onFilterChange" @clear-click="onFilterChange" />
                    <DatePicker v-model="filterDateTo" placeholder="Date To" dateFormat="yy-mm-dd" showIcon class="w-full" @date-select="onFilterChange" @clear-click="onFilterChange" />
                    <div class="flex items-end">
                        <Button icon="pi pi-filter-slash" severity="secondary" outlined @click="clearFilters" v-tooltip.top="'Clear filters'" />
                    </div>
                </div>

                <DataTable
                    :value="records"
                    :paginator="true"
                    :rows="rowsPerPage"
                    :totalRecords="totalRecords"
                    :lazy="true"
                    :loading="tableLoading"
                    :rowsPerPageOptions="[10, 25, 50]"
                    @page="onPage"
                    @sort="onSort"
                    dataKey="id"
                    :rowHover="true"
                    responsiveLayout="scroll"
                >
                    <template #empty>No attendance records found.</template>

                    <Column field="user_name" header="User" sortable style="min-width: 10rem" />
                    <Column field="type" header="Type" sortable style="min-width: 8rem">
                        <template #body="{ data }">
                            <Tag :value="data.type_display" :severity="getTypeSeverity(data.type)" />
                        </template>
                    </Column>
                    <Column field="captured_time" header="Captured Time" sortable style="min-width: 6rem">
                        <template #body="{ data }">
                            <span class="font-mono font-semibold">{{ data.captured_time || '—' }}</span>
                        </template>
                    </Column>
                    <Column field="branch_name" header="Branch" sortable style="min-width: 10rem">
                        <template #body="{ data }">
                            {{ data.branch_name || data.captured_branch || '—' }}
                        </template>
                    </Column>
                    <Column field="created_at" header="Date/Time" sortable style="min-width: 12rem">
                        <template #body="{ data }">
                            {{ new Date(data.created_at).toLocaleString() }}
                        </template>
                    </Column>
                    <Column field="method" header="Method" sortable style="min-width: 8rem">
                        <template #body="{ data }">
                            <div class="flex items-center gap-2">
                                <i :class="getMethodIcon(data.method)" class="text-muted-color"></i>
                                <span>{{ data.method_display }}</span>
                            </div>
                        </template>
                    </Column>
                    <Column field="status" header="Status" sortable style="min-width: 8rem">
                        <template #body="{ data }">
                            <Tag :value="data.status_display" :severity="getStatusSeverity(data.status)" />
                        </template>
                    </Column>
                    <Column field="image" header="Evidence" style="min-width: 6rem">
                        <template #body="{ data }">
                            <img v-if="data.image" :src="data.image" alt="Evidence" class="w-10 h-10 rounded object-cover cursor-pointer border border-surface-200 dark:border-surface-600" @click="openImagePreview(data.image)" />
                            <span v-else class="text-muted-color">—</span>
                        </template>
                    </Column>
                </DataTable>
            </div>
        </div>
    </div>

    <!-- Image Preview Dialog -->
    <Dialog v-model:visible="previewDialog" header="Image Evidence" :modal="true" :style="{ width: '600px' }">
        <div class="flex justify-center">
            <img :src="previewImage" alt="Attendance Evidence" class="max-w-full max-h-[70vh] rounded" />
        </div>
    </Dialog>

    <!-- Manual Request Dialog -->
    <Dialog v-model:visible="manualRequestDialog" header="Request Manual Attendance" :modal="true" :style="{ width: '450px' }">
        <form @submit.prevent="submitManualRequest">
            <div class="flex flex-col gap-4 mt-2">
                <p class="text-sm text-muted-color">If the OCR time is inaccurate, submit a manual clock in/out request to your admin for approval.</p>

                <div class="flex flex-col gap-2">
                    <label class="font-medium">Type *</label>
                    <Select v-model="manualRequest.type" :options="[{ label: 'Clock In', value: 'clock_in' }, { label: 'Clock Out', value: 'clock_out' }]" optionLabel="label" optionValue="value" placeholder="Select type" :invalid="manualSubmitted && !manualRequest.type" />
                </div>

                <div class="flex flex-col gap-2">
                    <label class="font-medium">Branch</label>
                    <Select v-model="manualRequest.branch" :options="branches" optionLabel="label" optionValue="value" placeholder="Select branch" showClear filter />
                </div>

                <div class="flex flex-col gap-2">
                    <label class="font-medium">Date *</label>
                    <DatePicker v-model="manualRequest.date" dateFormat="yy-mm-dd" placeholder="Select date" :invalid="manualSubmitted && !manualRequest.date" showIcon />
                </div>

                <div class="flex flex-col gap-2">
                    <label class="font-medium">Time (HH:MM) *</label>
                    <InputText v-model="manualRequest.time" placeholder="e.g. 08:30" :invalid="manualSubmitted && !manualRequest.time.trim()" />
                    <small v-if="manualSubmitted && !manualRequest.time.trim()" class="text-red-500">Time is required.</small>
                </div>

                <div class="flex flex-col gap-2">
                    <label class="font-medium">Reason *</label>
                    <Textarea v-model="manualRequest.reason" rows="3" placeholder="Why do you need a manual entry?" :invalid="manualSubmitted && !manualRequest.reason.trim()" />
                    <small v-if="manualSubmitted && !manualRequest.reason.trim()" class="text-red-500">Reason is required.</small>
                </div>
            </div>
            <div class="flex justify-end gap-2 mt-6">
                <Button label="Cancel" icon="pi pi-times" severity="secondary" @click="manualRequestDialog = false" type="button" />
                <Button type="submit" label="Submit Request" icon="pi pi-send" />
            </div>
        </form>
    </Dialog>
</template>
