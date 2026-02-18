<script setup>
import { ref, computed, onBeforeUnmount } from 'vue';
import { useToast } from 'primevue/usetoast';

const toast = useToast();

// --- State ---
const isClockedIn = ref(false);
const cameraActive = ref(false);
const videoRef = ref(null);
const canvasRef = ref(null);
const capturedImage = ref(null);
const ocrTime = ref('');
const ocrProcessing = ref(false);
const manualRequestDialog = ref(false);
const manualSubmitted = ref(false);
const stream = ref(null);

const manualRequest = ref({
    type: 'Clock In',
    date: null,
    time: '',
    reason: ''
});

// Mock attendance records
const attendanceRecords = ref([
    { id: 1, user: 'John Doe', type: 'Clock In', time: '2026-02-18 08:02:15', capturedTime: '08:02', method: 'Camera', status: 'Approved', photo: null },
    { id: 2, user: 'John Doe', type: 'Clock Out', time: '2026-02-18 17:05:30', capturedTime: '17:05', method: 'Camera', status: 'Approved', photo: null },
    { id: 3, user: 'Jane Smith', type: 'Clock In', time: '2026-02-18 08:15:00', capturedTime: '08:15', method: 'Camera', status: 'Approved', photo: null },
    { id: 4, user: 'Jane Smith', type: 'Clock Out', time: '2026-02-17 17:30:00', capturedTime: '17:30', method: 'Manual', status: 'Pending', photo: null },
    { id: 5, user: 'Bob Wilson', type: 'Clock In', time: '2026-02-17 07:55:00', capturedTime: '07:55', method: 'Camera', status: 'Approved', photo: null }
]);
const totalRecords = ref(attendanceRecords.value.length);
let nextId = 6;

const filterText = ref('');
const filteredRecords = computed(() => {
    if (!filterText.value.trim()) return attendanceRecords.value;
    const q = filterText.value.toLowerCase();
    return attendanceRecords.value.filter(
        (r) => r.user.toLowerCase().includes(q) || r.type.toLowerCase().includes(q) || r.method.toLowerCase().includes(q) || r.status.toLowerCase().includes(q)
    );
});

// --- Camera ---
const startCamera = async () => {
    try {
        const mediaStream = await navigator.mediaDevices.getUserMedia({
            video: { facingMode: 'environment', width: { ideal: 640 }, height: { ideal: 480 } }
        });
        stream.value = mediaStream;
        cameraActive.value = true;
        capturedImage.value = null;
        ocrTime.value = '';

        // Wait for next tick so videoRef is rendered
        await new Promise((r) => setTimeout(r, 100));
        if (videoRef.value) {
            videoRef.value.srcObject = mediaStream;
            videoRef.value.play();
        }
    } catch (err) {
        toast.add({ severity: 'error', summary: 'Camera Error', detail: 'Could not access camera. Please grant permission.', life: 4000 });
    }
};

const stopCamera = () => {
    if (stream.value) {
        stream.value.getTracks().forEach((track) => track.stop());
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
    stopCamera();

    // Simulate OCR — extract time from the image
    runOCR();
};

const runOCR = () => {
    ocrProcessing.value = true;
    // TODO: Integrate real OCR (Tesseract.js or backend OCR endpoint)
    // For now simulate extracting the current time
    setTimeout(() => {
        const now = new Date();
        ocrTime.value = now.toLocaleTimeString('en-AU', { hour: '2-digit', minute: '2-digit', hour12: false });
        ocrProcessing.value = false;
        toast.add({ severity: 'info', summary: 'OCR Complete', detail: `Detected time: ${ocrTime.value}`, life: 3000 });
    }, 1500);
};

const retakePhoto = () => {
    capturedImage.value = null;
    ocrTime.value = '';
    startCamera();
};

// --- Clock In / Out ---
const submitAttendance = () => {
    const type = isClockedIn.value ? 'Clock Out' : 'Clock In';
    const now = new Date();

    attendanceRecords.value.unshift({
        id: nextId++,
        user: 'Current User',
        type,
        time: now.toISOString().replace('T', ' ').slice(0, 19),
        capturedTime: ocrTime.value || now.toLocaleTimeString('en-AU', { hour: '2-digit', minute: '2-digit', hour12: false }),
        method: 'Camera',
        status: 'Approved',
        photo: capturedImage.value
    });
    totalRecords.value = attendanceRecords.value.length;

    isClockedIn.value = !isClockedIn.value;
    capturedImage.value = null;
    ocrTime.value = '';

    toast.add({
        severity: 'success',
        summary: type,
        detail: `${type} recorded successfully at ${now.toLocaleTimeString('en-AU', { hour: '2-digit', minute: '2-digit', hour12: false })}`,
        life: 3000
    });
};

// --- Manual Request ---
const openManualRequest = () => {
    manualRequest.value = { type: 'Clock In', date: null, time: '', reason: '' };
    manualSubmitted.value = false;
    manualRequestDialog.value = true;
};

const submitManualRequest = () => {
    manualSubmitted.value = true;
    if (!manualRequest.value.date || !manualRequest.value.time.trim() || !manualRequest.value.reason.trim()) return;

    const d = new Date(manualRequest.value.date);
    const dateStr = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;

    attendanceRecords.value.unshift({
        id: nextId++,
        user: 'Current User',
        type: manualRequest.value.type,
        time: `${dateStr} ${manualRequest.value.time}:00`,
        capturedTime: manualRequest.value.time,
        method: 'Manual',
        status: 'Pending',
        photo: null
    });
    totalRecords.value = attendanceRecords.value.length;

    manualRequestDialog.value = false;
    toast.add({ severity: 'warn', summary: 'Manual Request Sent', detail: 'Your manual attendance request has been sent to the admin for approval.', life: 4000 });
};

const getTypeSeverity = (type) => (type === 'Clock In' ? 'success' : 'info');
const getStatusSeverity = (status) => {
    if (status === 'Approved') return 'success';
    if (status === 'Pending') return 'warn';
    return 'danger';
};
const getMethodIcon = (method) => (method === 'Camera' ? 'pi pi-camera' : 'pi pi-pencil');

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
                                <span class="text-white text-sm">Extracting time...</span>
                            </div>
                            <div v-else-if="ocrTime" class="absolute bottom-0 left-0 right-0 bg-black/60 p-2 text-center">
                                <span class="text-white text-sm">Detected Time: </span>
                                <span class="text-white font-bold text-lg">{{ ocrTime }}</span>
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
                            <Button :label="isClockedIn ? 'Confirm Clock Out' : 'Confirm Clock In'" :icon="isClockedIn ? 'pi pi-sign-out' : 'pi pi-check'" @click="submitAttendance" class="flex-1" :severity="isClockedIn ? 'warn' : 'success'" />
                            <Button label="Retake" icon="pi pi-refresh" severity="secondary" outlined @click="retakePhoto" />
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

                <div class="mb-4">
                    <IconField>
                        <InputIcon class="pi pi-search" />
                        <InputText v-model="filterText" placeholder="Search records..." class="w-full" />
                    </IconField>
                </div>

                <DataTable :value="filteredRecords" :paginator="true" :rows="10" dataKey="id" :rowHover="true" responsiveLayout="scroll">
                    <template #empty>No attendance records found.</template>

                    <Column field="user" header="User" sortable style="min-width: 10rem" />
                    <Column field="type" header="Type" sortable style="min-width: 8rem">
                        <template #body="{ data }">
                            <Tag :value="data.type" :severity="getTypeSeverity(data.type)" />
                        </template>
                    </Column>
                    <Column field="capturedTime" header="Time" sortable style="min-width: 6rem">
                        <template #body="{ data }">
                            <span class="font-mono font-semibold">{{ data.capturedTime }}</span>
                        </template>
                    </Column>
                    <Column field="time" header="Date/Time" sortable style="min-width: 12rem" />
                    <Column field="method" header="Method" sortable style="min-width: 8rem">
                        <template #body="{ data }">
                            <div class="flex items-center gap-2">
                                <i :class="getMethodIcon(data.method)" class="text-muted-color"></i>
                                <span>{{ data.method }}</span>
                            </div>
                        </template>
                    </Column>
                    <Column field="status" header="Status" sortable style="min-width: 8rem">
                        <template #body="{ data }">
                            <Tag :value="data.status" :severity="getStatusSeverity(data.status)" />
                        </template>
                    </Column>
                </DataTable>
            </div>
        </div>
    </div>

    <!-- Manual Request Dialog -->
    <Dialog v-model:visible="manualRequestDialog" header="Request Manual Attendance" :modal="true" :style="{ width: '450px' }">
        <form @submit.prevent="submitManualRequest">
            <div class="flex flex-col gap-4 mt-2">
                <p class="text-sm text-muted-color">If the OCR time is inaccurate, submit a manual clock in/out request to your admin for approval.</p>

                <div class="flex flex-col gap-2">
                    <label class="font-medium">Type *</label>
                    <Select v-model="manualRequest.type" :options="['Clock In', 'Clock Out']" placeholder="Select type" :invalid="manualSubmitted && !manualRequest.type" />
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
