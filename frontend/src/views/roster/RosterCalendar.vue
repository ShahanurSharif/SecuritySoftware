<script setup>
import { ref, computed, watch, onMounted } from 'vue';
import { useToast } from 'primevue/usetoast';
import api from '@/services/api';

const props = defineProps({
    branches: Array,
    users: Array,
    shiftTemplates: Array,
    isAdmin: Boolean
});

const emit = defineEmits(['add-shift', 'copy-week']);
const toast = useToast();

// ─── State ─────────────────────────────────────────────────────
const calendarMonth = ref(new Date().toISOString().slice(0, 7));
const calendarShifts = ref([]);
const calendarLoading = ref(false);

const fmtDate = (d) => {
    const y = d.getFullYear();
    const m = String(d.getMonth() + 1).padStart(2, '0');
    const day = String(d.getDate()).padStart(2, '0');
    return `${y}-${m}-${day}`;
};

const today = computed(() => fmtDate(new Date()));

const calendarDays = computed(() => {
    const [year, month] = calendarMonth.value.split('-').map(Number);
    const firstDay = new Date(year, month - 1, 1);
    const lastDay = new Date(year, month, 0);
    const startPad = firstDay.getDay() === 0 ? 6 : firstDay.getDay() - 1;

    const days = [];
    for (let i = startPad; i > 0; i--) {
        const d = new Date(year, month - 1, 1 - i);
        days.push({ date: fmtDate(d), inMonth: false, shifts: [] });
    }
    for (let d = 1; d <= lastDay.getDate(); d++) {
        const dt = new Date(year, month - 1, d);
        const dateStr = fmtDate(dt);
        days.push({
            date: dateStr,
            inMonth: true,
            day: d,
            shifts: calendarShifts.value.filter((s) => s.date === dateStr)
        });
    }
    while (days.length % 7 !== 0) {
        const last = new Date(days[days.length - 1].date);
        last.setDate(last.getDate() + 1);
        days.push({ date: fmtDate(last), inMonth: false, shifts: [] });
    }
    return days;
});

const monthLabel = computed(() => {
    const [y, m] = calendarMonth.value.split('-').map(Number);
    return new Date(y, m - 1).toLocaleString('default', { month: 'long', year: 'numeric' });
});

const monthTotalHours = computed(() => {
    return calendarShifts.value.reduce((sum, s) => sum + (s.total_hours || 0), 0).toFixed(1);
});
const monthTotalPay = computed(() => {
    return calendarShifts.value.reduce((sum, s) => sum + (s.total_pay || 0), 0).toFixed(2);
});

const dayTotalHours = (day) => {
    if (!day.shifts?.length) return 0;
    return day.shifts.reduce((sum, s) => sum + (s.total_hours || 0), 0).toFixed(1);
};

// ─── Fetch ─────────────────────────────────────────────────────
const fetchCalendarShifts = async () => {
    calendarLoading.value = true;
    try {
        const { data } = await api.get('/roster/shifts/calendar/', { params: { month: calendarMonth.value } });
        calendarShifts.value = data;
    } catch {
        toast.add({ severity: 'error', summary: 'Error', detail: 'Failed to load calendar shifts.', life: 4000 });
    } finally {
        calendarLoading.value = false;
    }
};

const prevMonth = () => {
    const [y, m] = calendarMonth.value.split('-').map(Number);
    const d = new Date(y, m - 2, 1);
    calendarMonth.value = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`;
};
const nextMonth = () => {
    const [y, m] = calendarMonth.value.split('-').map(Number);
    const d = new Date(y, m, 1);
    calendarMonth.value = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`;
};

watch(calendarMonth, fetchCalendarShifts);

const onDayClick = (day) => {
    if (!props.isAdmin) return;
    emit('add-shift', day.date);
};

const refresh = () => fetchCalendarShifts();
defineExpose({ refresh });

onMounted(fetchCalendarShifts);
</script>

<template>
    <div class="card">
        <div class="flex items-center justify-between mb-4">
            <Button icon="pi pi-chevron-left" text rounded @click="prevMonth" />
            <span class="text-lg font-bold">{{ monthLabel }}</span>
            <Button icon="pi pi-chevron-right" text rounded @click="nextMonth" />
        </div>

        <ProgressBar v-if="calendarLoading" mode="indeterminate" class="mb-2" style="height: 3px" />

        <!-- Month totals -->
        <div class="flex gap-6 mb-3 text-sm">
            <div class="flex items-center gap-2">
                <i class="pi pi-clock text-primary"></i>
                <span class="font-semibold">{{ monthTotalHours }}h</span>
                <span class="text-muted-color">total hours</span>
            </div>
            <div class="flex items-center gap-2">
                <i class="pi pi-dollar text-green-500"></i>
                <span class="font-semibold">${{ monthTotalPay }}</span>
                <span class="text-muted-color">total pay</span>
            </div>
            <div class="flex items-center gap-2">
                <i class="pi pi-calendar text-blue-500"></i>
                <span class="font-semibold">{{ calendarShifts.length }}</span>
                <span class="text-muted-color">shifts</span>
            </div>
        </div>

        <div class="grid grid-cols-7 gap-px bg-surface-200 dark:bg-surface-700 rounded-lg overflow-hidden">
            <div v-for="d in ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']" :key="d" class="bg-surface-100 dark:bg-surface-800 text-center py-2 font-semibold text-sm">
                {{ d }}
            </div>
            <div
                v-for="(day, i) in calendarDays"
                :key="i"
                class="bg-surface-0 dark:bg-surface-900 min-h-24 p-1 cursor-pointer hover:bg-surface-50 dark:hover:bg-surface-800 transition-colors"
                :class="{
                    'opacity-40': !day.inMonth,
                    'ring-2 ring-primary': day.date === today
                }"
                @click="onDayClick(day)"
            >
                <div class="text-xs font-medium mb-1" :class="day.date === today ? 'text-primary font-bold' : ''">
                    {{ day.day }}
                </div>
                <div v-for="s in day.shifts?.slice(0, 3)" :key="s.id" class="text-xs rounded px-1 mb-0.5 truncate text-white" :style="{ backgroundColor: s.template_name ? '#3B82F6' : '#6B7280' }">
                    {{ s.start_time?.slice(0, 5) }} {{ s.user_name?.split(' ')[0] }} <span class="opacity-75">{{ s.total_hours }}h</span>
                </div>
                <div v-if="day.shifts?.length > 3" class="text-xs text-muted-color">+{{ day.shifts.length - 3 }} more</div>
                <div v-if="dayTotalHours(day) > 0" class="text-xs font-bold text-primary mt-0.5">{{ dayTotalHours(day) }}h</div>
            </div>
        </div>

        <div v-if="isAdmin" class="flex gap-2 mt-4">
            <Button label="Add Shift" icon="pi pi-plus" @click="emit('add-shift', '')" />
            <Button label="Copy Week" icon="pi pi-copy" severity="secondary" @click="emit('copy-week')" />
        </div>
    </div>
</template>
