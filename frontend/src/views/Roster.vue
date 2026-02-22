<script setup>
import { ref, computed, onMounted, nextTick } from 'vue';
import api from '@/services/api';

import RosterCalendar from './roster/RosterCalendar.vue';
import RosterShifts from './roster/RosterShifts.vue';
import RosterTemplates from './roster/RosterTemplates.vue';
import RosterAvailability from './roster/RosterAvailability.vue';
import RosterPTO from './roster/RosterPTO.vue';
import RosterDropRequests from './roster/RosterDropRequests.vue';
import RosterNotifications from './roster/RosterNotifications.vue';

// ─── Active Tab ────────────────────────────────────────────────
const activeTab = ref(0);

// ─── Shared Lookups ────────────────────────────────────────────
const branches = ref([]);
const users = ref([]);
const shiftTemplates = ref([]);
const userRole = ref('Admin');
const unreadCount = ref(0);

const fetchBranches = async () => {
    try {
        const { data } = await api.get('/branches/', { params: { page_size: 1000 } });
        branches.value = (data.results || data).map((b) => ({ label: b.name, value: b.id }));
    } catch { /* silent */ }
};

const fetchUsers = async () => {
    try {
        const { data } = await api.get('/profiles/', { params: { page_size: 1000 } });
        users.value = (data.results || data).map((p) => ({
            label: `${p.user?.first_name || ''} ${p.user?.last_name || ''}`.trim() || p.user?.username,
            value: p.user?.id,
            role: p.role
        }));
    } catch { /* silent */ }
};

const fetchTemplates = async () => {
    try {
        const { data } = await api.get('/roster/shift-templates/', { params: { page_size: 1000 } });
        shiftTemplates.value = data.results || data;
    } catch { /* silent */ }
};

const fetchCurrentUser = async () => {
    try {
        const { data } = await api.get('/auth/me/');
        userRole.value = data.role;
    } catch { /* silent */ }
};

const isAdmin = computed(() => userRole.value === 'Admin');

// ─── Template refs ─────────────────────────────────────────────
const calendarRef = ref(null);
const shiftsRef = ref(null);
const templatesRef = ref(null);

// ─── Cross-component events ────────────────────────────────────
const onAddShift = (date) => {
    activeTab.value = 1;
    nextTick(() => shiftsRef.value?.openNewShift(date));
};

const onCopyWeek = () => {
    activeTab.value = 1;
    nextTick(() => shiftsRef.value?.openCopyWeek());
};

const onRefreshCalendar = () => calendarRef.value?.refresh();

const onTemplatesUpdated = () => fetchTemplates();

const onUnreadCount = (count) => { unreadCount.value = count; };

// ─── Init ──────────────────────────────────────────────────────
onMounted(async () => {
    await Promise.all([fetchCurrentUser(), fetchBranches(), fetchUsers(), fetchTemplates()]);
});
</script>

<template>
    <div class="flex flex-col gap-4">
        <div class="font-semibold text-xl">Roster Management</div>

        <Tabs v-model:value="activeTab">
            <TabList>
                <Tab :value="0"><i class="pi pi-calendar mr-2"></i>Calendar</Tab>
                <Tab :value="1"><i class="pi pi-list mr-2"></i>Shifts</Tab>
                <Tab :value="2"><i class="pi pi-clock mr-2"></i>Templates</Tab>
                <Tab :value="3"><i class="pi pi-check-circle mr-2"></i>Availability</Tab>
                <Tab :value="4"><i class="pi pi-calendar-minus mr-2"></i>PTO</Tab>
                <Tab :value="5"><i class="pi pi-arrow-down mr-2"></i>Drop Requests</Tab>
                <Tab :value="6">
                    <i class="pi pi-bell mr-2"></i>Notifications
                    <Badge v-if="unreadCount > 0" :value="unreadCount" severity="danger" class="ml-2" />
                </Tab>
            </TabList>

            <TabPanels>
                <TabPanel :value="0">
                    <RosterCalendar ref="calendarRef" :branches="branches" :users="users" :shiftTemplates="shiftTemplates" :isAdmin="isAdmin" @add-shift="onAddShift" @copy-week="onCopyWeek" />
                </TabPanel>

                <TabPanel :value="1">
                    <RosterShifts ref="shiftsRef" :branches="branches" :users="users" :shiftTemplates="shiftTemplates" :isAdmin="isAdmin" @refresh-calendar="onRefreshCalendar" />
                </TabPanel>

                <TabPanel :value="2">
                    <RosterTemplates ref="templatesRef" :branches="branches" :isAdmin="isAdmin" @templates-updated="onTemplatesUpdated" />
                </TabPanel>

                <TabPanel :value="3">
                    <RosterAvailability :branches="branches" :users="users" :isAdmin="isAdmin" />
                </TabPanel>

                <TabPanel :value="4">
                    <RosterPTO :users="users" :isAdmin="isAdmin" />
                </TabPanel>

                <TabPanel :value="5">
                    <RosterDropRequests :isAdmin="isAdmin" />
                </TabPanel>

                <TabPanel :value="6">
                    <RosterNotifications @unread-count="onUnreadCount" />
                </TabPanel>
            </TabPanels>
        </Tabs>
    </div>
</template>
