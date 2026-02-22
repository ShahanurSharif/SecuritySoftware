<script setup>
import { ref, computed, onMounted, watch } from 'vue';
import { useToast } from 'primevue/usetoast';
import api from '@/services/api';

const props = defineProps({
    branches: Array,
    users: Array,
    isAdmin: Boolean
});

const toast = useToast();

// ─── Week navigation ───────────────────────────────────────────
const fmtDate = (d) => {
    const y = d.getFullYear();
    const m = String(d.getMonth() + 1).padStart(2, '0');
    const day = String(d.getDate()).padStart(2, '0');
    return `${y}-${m}-${day}`;
};

const getMonday = (d) => {
    const dt = new Date(d);
    const day = dt.getDay();
    const diff = dt.getDate() - day + (day === 0 ? -6 : 1);
    return new Date(dt.setDate(diff));
};

const weekStart = ref(fmtDate(getMonday(new Date())));
const matrixData = ref(null);
const matrixLoading = ref(false);

const weekDates = computed(() => {
    if (!matrixData.value?.dates) return [];
    return matrixData.value.dates;
});

const weekLabel = computed(() => {
    if (!matrixData.value) return '';
    const s = new Date(matrixData.value.week_start);
    const e = new Date(matrixData.value.week_end);
    return `${s.toLocaleDateString('default', { month: 'short', day: 'numeric' })} – ${e.toLocaleDateString('default', { month: 'short', day: 'numeric', year: 'numeric' })}`;
});

const dayLabels = computed(() => {
    return weekDates.value.map((d) => {
        const dt = new Date(d + 'T00:00:00');
        return { date: d, short: dt.toLocaleDateString('default', { weekday: 'short' }), num: dt.getDate() };
    });
});

const prevWeek = () => {
    const d = new Date(weekStart.value);
    d.setDate(d.getDate() - 7);
    weekStart.value = fmtDate(d);
};

const nextWeek = () => {
    const d = new Date(weekStart.value);
    d.setDate(d.getDate() + 7);
    weekStart.value = fmtDate(d);
};

const goToday = () => {
    weekStart.value = fmtDate(getMonday(new Date()));
};

// ─── Fetch matrix ──────────────────────────────────────────────
const fetchMatrix = async () => {
    matrixLoading.value = true;
    try {
        const { data } = await api.get('/roster/availability/lpo_matrix/', { params: { week_start: weekStart.value } });
        matrixData.value = data;
    } catch {
        toast.add({ severity: 'error', summary: 'Error', detail: 'Failed to load availability matrix.', life: 4000 });
    } finally {
        matrixLoading.value = false;
    }
};

watch(weekStart, fetchMatrix);

// ─── Availability Dialog ───────────────────────────────────────
const availDialog = ref(false);
const availSubmitted = ref(false);

const presetOptions = [
    { label: 'Whole Day', value: 'whole_day', icon: 'pi pi-sun', desc: '00:00 – 23:59', severity: 'success' },
    { label: 'Day Only', value: 'day_only', icon: 'pi pi-sun', desc: '06:00 – 18:00', severity: 'info' },
    { label: 'Night Only', value: 'night_only', icon: 'pi pi-moon', desc: '18:00 – 06:00', severity: 'warn' },
    { label: 'From Time', value: 'from_time', icon: 'pi pi-arrow-right', desc: 'Available from...', severity: 'contrast' },
    { label: 'Custom', value: 'custom', icon: 'pi pi-sliders-h', desc: 'Set times', severity: 'secondary' }
];

const PRESET_TIMES = {
    whole_day: { start: '00:00', end: '23:59' },
    day_only: { start: '06:00', end: '18:00' },
    night_only: { start: '18:00', end: '06:00' }
};

const emptyAvailForm = { user: null, user_name: '', date: '', preset: 'whole_day', start_time: '00:00', end_time: '23:59', is_available: true, notes: '' };
const availForm = ref({ ...emptyAvailForm });

const onPresetChange = (val) => {
    availForm.value.preset = val;
    if (PRESET_TIMES[val]) {
        availForm.value.start_time = PRESET_TIMES[val].start;
        availForm.value.end_time = PRESET_TIMES[val].end;
    } else if (val === 'from_time') {
        availForm.value.start_time = '';
        availForm.value.end_time = '23:59';
    }
};

const openAvailCell = (user, dateStr, existing) => {
    if (!props.isAdmin) return;
    if (existing) {
        availForm.value = {
            user: user.user_id,
            user_name: user.user_name,
            date: dateStr,
            preset: existing.preset || 'custom',
            start_time: existing.start_time?.slice(0, 5) || '00:00',
            end_time: existing.end_time?.slice(0, 5) || '23:59',
            is_available: existing.is_available,
            notes: existing.notes || ''
        };
    } else {
        availForm.value = {
            ...emptyAvailForm,
            user: user.user_id,
            user_name: user.user_name,
            date: dateStr
        };
    }
    availSubmitted.value = false;
    availDialog.value = true;
};

const saveAvail = async () => {
    availSubmitted.value = true;
    if (!availForm.value.user || !availForm.value.date) return;
    try {
        const payload = {
            user: availForm.value.user,
            date: availForm.value.date,
            preset: availForm.value.preset,
            is_available: availForm.value.is_available,
            notes: availForm.value.notes
        };
        if (availForm.value.preset === 'from_time') {
            payload.start_time = availForm.value.start_time;
        } else if (availForm.value.preset === 'custom') {
            payload.start_time = availForm.value.start_time;
            payload.end_time = availForm.value.end_time;
        }
        await api.post('/roster/availability/quick_set/', payload);
        toast.add({ severity: 'success', summary: 'Saved', detail: 'Availability updated.', life: 3000 });
        availDialog.value = false;
        fetchMatrix();
    } catch (err) {
        const detail = err.response?.data?.error || err.response?.data?.detail || 'Save failed.';
        toast.add({ severity: 'error', summary: 'Error', detail, life: 5000 });
    }
};

const removeAvail = async () => {
    try {
        await api.post('/roster/availability/remove_date/', {
            user: availForm.value.user,
            date: availForm.value.date
        });
        toast.add({ severity: 'success', summary: 'Removed', detail: 'Availability cleared.', life: 3000 });
        availDialog.value = false;
        fetchMatrix();
    } catch {
        toast.add({ severity: 'error', summary: 'Error', detail: 'Remove failed.', life: 4000 });
    }
};

// ─── Cell display helpers ──────────────────────────────────────
// ─── Time formatting helpers ───────────────────────────────────
const fmt12h = (timeStr) => {
    if (!timeStr) return '';
    const [h, m] = timeStr.slice(0, 5).split(':').map(Number);
    const suffix = h >= 12 ? 'PM' : 'AM';
    const hour12 = h === 0 ? 12 : h > 12 ? h - 12 : h;
    return m === 0 ? `${hour12}${suffix}` : `${hour12}:${String(m).padStart(2, '0')}${suffix}`;
};

const cellColor = (avail) => {
    if (!avail) return 'bg-surface-100 dark:bg-surface-800 text-muted-color';
    if (!avail.is_available) return 'bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400 border-red-200 dark:border-red-800';
    const colors = {
        whole_day: 'bg-green-50 dark:bg-green-900/20 text-green-700 dark:text-green-400 border-green-200 dark:border-green-700',
        day_only: 'bg-blue-50 dark:bg-blue-900/20 text-blue-700 dark:text-blue-400 border-blue-200 dark:border-blue-700',
        night_only: 'bg-amber-50 dark:bg-amber-900/20 text-amber-700 dark:text-amber-400 border-amber-200 dark:border-amber-700',
        from_time: 'bg-teal-50 dark:bg-teal-900/20 text-teal-700 dark:text-teal-400 border-teal-200 dark:border-teal-700',
        custom: 'bg-purple-50 dark:bg-purple-900/20 text-purple-700 dark:text-purple-400 border-purple-200 dark:border-purple-700'
    };
    return colors[avail.preset] || colors.custom;
};

const cellLabel = (avail) => {
    if (!avail) return '—';
    if (!avail.is_available) return 'OFF';
    if (avail.preset === 'whole_day') return 'All Day';
    if (avail.preset === 'day_only') return 'Day';
    if (avail.preset === 'night_only') return 'Night';
    if (avail.preset === 'from_time') return `From ${fmt12h(avail.start_time)}`;
    // custom — show range
    return `${fmt12h(avail.start_time)}–${fmt12h(avail.end_time)}`;
};

const cellTime = (avail) => {
    if (!avail || !avail.is_available) return '';
    if (avail.preset === 'from_time') return `${fmt12h(avail.start_time)} onwards`;
    return `${fmt12h(avail.start_time)} – ${fmt12h(avail.end_time)}`;
};

// ─── LPO users from the users prop ────────────────────────────
const lpoUsers = computed(() => {
    return matrixData.value?.users || [];
});

const refresh = () => fetchMatrix();
defineExpose({ refresh });

onMounted(fetchMatrix);
</script>

<template>
    <div class="card">
        <!-- Header -->
        <div class="flex items-center justify-between mb-4">
            <span class="font-semibold text-lg">LPO Availability</span>
            <div class="flex items-center gap-2">
                <Button icon="pi pi-chevron-left" text rounded @click="prevWeek" />
                <Button label="Today" text size="small" @click="goToday" />
                <span class="font-semibold text-sm min-w-48 text-center">{{ weekLabel }}</span>
                <Button icon="pi pi-chevron-right" text rounded @click="nextWeek" />
            </div>
        </div>

        <!-- Legend -->
        <div class="flex flex-wrap gap-4 mb-3 text-xs">
            <div class="flex items-center gap-1"><div class="w-3 h-3 rounded bg-green-400"></div> All Day</div>
            <div class="flex items-center gap-1"><div class="w-3 h-3 rounded bg-blue-400"></div> Day Only</div>
            <div class="flex items-center gap-1"><div class="w-3 h-3 rounded bg-amber-400"></div> Night Only</div>
            <div class="flex items-center gap-1"><div class="w-3 h-3 rounded bg-teal-400"></div> From Time</div>
            <div class="flex items-center gap-1"><div class="w-3 h-3 rounded bg-purple-400"></div> Custom</div>
            <div class="flex items-center gap-1"><div class="w-3 h-3 rounded bg-red-400"></div> Off</div>
            <div class="flex items-center gap-1"><div class="w-3 h-3 rounded bg-surface-300"></div> Not Set</div>
        </div>

        <ProgressBar v-if="matrixLoading" mode="indeterminate" class="mb-2" style="height: 3px" />

        <!-- Matrix Grid -->
        <div v-if="lpoUsers.length > 0" class="overflow-x-auto">
            <table class="w-full border-collapse text-sm">
                <thead>
                    <tr>
                        <th class="text-left py-2 px-3 bg-surface-100 dark:bg-surface-800 rounded-tl-lg min-w-40">LPO Officer</th>
                        <th v-for="dl in dayLabels" :key="dl.date" class="text-center py-2 px-2 bg-surface-100 dark:bg-surface-800 min-w-24" :class="{ 'font-bold text-primary': dl.date === fmtDate(new Date()) }">
                            <div>{{ dl.short }}</div>
                            <div class="text-xs text-muted-color">{{ dl.num }}</div>
                        </th>
                    </tr>
                </thead>
                <tbody>
                    <tr v-for="user in lpoUsers" :key="user.user_id" class="border-b border-surface-200 dark:border-surface-700">
                        <td class="py-2 px-3 font-medium">{{ user.user_name }}</td>
                        <td v-for="dl in dayLabels" :key="dl.date" class="py-1 px-1 text-center">
                            <div
                                class="rounded-lg p-1.5 border cursor-pointer transition-all hover:scale-105 hover:shadow-md min-h-12 flex flex-col items-center justify-center"
                                :class="cellColor(user.days[dl.date])"
                                @click="openAvailCell(user, dl.date, user.days[dl.date])"
                            >
                                <div class="font-semibold text-xs">{{ cellLabel(user.days[dl.date]) }}</div>
                                <div class="text-[10px] opacity-75">{{ cellTime(user.days[dl.date]) }}</div>
                            </div>
                        </td>
                    </tr>
                </tbody>
            </table>
        </div>

        <div v-else-if="!matrixLoading" class="text-center py-12 text-muted-color">
            <i class="pi pi-users text-4xl mb-3"></i>
            <p>No LPO users found. Make sure users have the LPO role assigned.</p>
        </div>
    </div>

    <!-- ═══════ AVAILABILITY DIALOG ═══════ -->
    <Dialog v-model:visible="availDialog" header="Set Availability" modal style="width: 28rem">
        <div class="flex flex-col gap-4">
            <!-- User & Date (read-only context) -->
            <div class="bg-surface-100 dark:bg-surface-800 rounded-lg p-3">
                <div class="font-semibold">{{ availForm.user_name }}</div>
                <div class="text-sm text-muted-color">{{ new Date(availForm.date + 'T00:00:00').toLocaleDateString('default', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' }) }}</div>
            </div>

            <!-- Available toggle -->
            <div class="flex items-center gap-3">
                <ToggleSwitch v-model="availForm.is_available" />
                <label class="font-semibold text-sm">{{ availForm.is_available ? 'Available' : 'Day Off / Unavailable' }}</label>
            </div>

            <!-- Preset shortcuts -->
            <div v-if="availForm.is_available" class="flex flex-col gap-2">
                <label class="font-semibold text-sm">Quick Select</label>
                <div class="grid grid-cols-2 gap-2">
                    <div
                        v-for="p in presetOptions"
                        :key="p.value"
                        class="border rounded-lg p-3 cursor-pointer transition-all hover:shadow-md text-center"
                        :class="availForm.preset === p.value ? 'border-primary bg-primary-50 dark:bg-primary-900/20 ring-2 ring-primary' : 'border-surface-200 dark:border-surface-700'"
                        @click="onPresetChange(p.value)"
                    >
                        <i :class="p.icon" class="text-lg mb-1"></i>
                        <div class="font-semibold text-sm">{{ p.label }}</div>
                        <div class="text-xs text-muted-color">{{ p.desc }}</div>
                    </div>
                </div>
            </div>

            <!-- From Time input (start only) -->
            <div v-if="availForm.is_available && availForm.preset === 'from_time'" class="flex flex-col gap-1">
                <label class="font-semibold text-sm">Available From *</label>
                <InputMask v-model="availForm.start_time" mask="99:99" placeholder="HH:MM" :class="{ 'p-invalid': availSubmitted && !availForm.start_time }" />
                <span class="text-xs text-muted-color">Until end of day (23:59)</span>
            </div>

            <!-- Custom time inputs (start + end) -->
            <div v-if="availForm.is_available && availForm.preset === 'custom'" class="grid grid-cols-2 gap-3">
                <div class="flex flex-col gap-1">
                    <label class="font-semibold text-sm">Start Time *</label>
                    <InputMask v-model="availForm.start_time" mask="99:99" placeholder="HH:MM" :class="{ 'p-invalid': availSubmitted && !availForm.start_time }" />
                </div>
                <div class="flex flex-col gap-1">
                    <label class="font-semibold text-sm">End Time *</label>
                    <InputMask v-model="availForm.end_time" mask="99:99" placeholder="HH:MM" :class="{ 'p-invalid': availSubmitted && !availForm.end_time }" />
                </div>
            </div>

            <!-- Notes -->
            <div class="flex flex-col gap-1">
                <label class="font-semibold text-sm">Notes</label>
                <InputText v-model="availForm.notes" placeholder="Optional notes..." />
            </div>
        </div>

        <template #footer>
            <Button label="Remove" icon="pi pi-trash" severity="danger" text @click="removeAvail" />
            <div class="flex-1"></div>
            <Button label="Cancel" text @click="availDialog = false" />
            <Button label="Save" icon="pi pi-check" @click="saveAvail" />
        </template>
    </Dialog>
</template>
