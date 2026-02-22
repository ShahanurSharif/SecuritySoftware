<script setup>
import { ref, onMounted } from 'vue';
import { useToast } from 'primevue/usetoast';
import api from '@/services/api';

const emit = defineEmits(['unread-count']);
const toast = useToast();

// ─── State ─────────────────────────────────────────────────────
const notifications = ref([]);
const notiLoading = ref(false);
const unreadCount = ref(0);

// ─── Fetch ─────────────────────────────────────────────────────
const fetchNotifications = async () => {
    notiLoading.value = true;
    try {
        const { data } = await api.get('/roster/notifications/', { params: { page_size: 100, ordering: '-sent_at' } });
        notifications.value = data.results || data;
    } catch {
        toast.add({ severity: 'error', summary: 'Error', detail: 'Failed to load notifications.', life: 4000 });
    } finally {
        notiLoading.value = false;
    }
};

const fetchUnreadCount = async () => {
    try {
        const { data } = await api.get('/roster/notifications/unread_count/');
        unreadCount.value = data.count;
        emit('unread-count', data.count);
    } catch { /* silent */ }
};

const markRead = async (n) => {
    if (n.is_read) return;
    try {
        await api.post(`/roster/notifications/${n.id}/mark_read/`);
        n.is_read = true;
        unreadCount.value = Math.max(0, unreadCount.value - 1);
        emit('unread-count', unreadCount.value);
    } catch { /* silent */ }
};

const markAllRead = async () => {
    try {
        await api.post('/roster/notifications/mark_all_read/');
        notifications.value.forEach((n) => (n.is_read = true));
        unreadCount.value = 0;
        emit('unread-count', 0);
        toast.add({ severity: 'success', summary: 'Done', detail: 'All marked as read.', life: 3000 });
    } catch {
        toast.add({ severity: 'error', summary: 'Error', detail: 'Failed.', life: 4000 });
    }
};

const refresh = () => { fetchNotifications(); fetchUnreadCount(); };
defineExpose({ refresh, fetchUnreadCount });

onMounted(() => { fetchNotifications(); fetchUnreadCount(); });
</script>

<template>
    <div class="card">
        <div class="flex justify-between items-center mb-4">
            <span class="font-semibold text-lg">Notifications</span>
            <Button v-if="unreadCount > 0" label="Mark All Read" icon="pi pi-check" severity="secondary" @click="markAllRead" />
        </div>

        <div v-if="notiLoading" class="text-center py-4">
            <ProgressSpinner style="width: 40px; height: 40px" />
        </div>

        <div v-else-if="notifications.length === 0" class="text-center py-8 text-muted-color">No notifications.</div>

        <div v-else class="flex flex-col gap-2">
            <div
                v-for="n in notifications"
                :key="n.id"
                class="flex items-start gap-3 p-3 rounded-lg border transition-colors cursor-pointer"
                :class="n.is_read ? 'bg-surface-0 dark:bg-surface-900 border-surface-200 dark:border-surface-700' : 'bg-primary-50 dark:bg-primary-900/20 border-primary-200 dark:border-primary-700'"
                @click="markRead(n)"
            >
                <i class="pi pi-bell mt-1" :class="n.is_read ? 'text-muted-color' : 'text-primary'"></i>
                <div class="flex-1">
                    <div class="font-semibold text-sm">{{ n.title }}</div>
                    <div class="text-sm text-muted-color mt-0.5">{{ n.message }}</div>
                    <div class="text-xs text-muted-color mt-1">{{ new Date(n.sent_at).toLocaleString() }}</div>
                </div>
                <Tag :value="n.type_display" size="small" />
            </div>
        </div>
    </div>
</template>
