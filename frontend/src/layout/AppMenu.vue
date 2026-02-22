<script setup>
import { ref } from 'vue';
import AppMenuItem from './AppMenuItem.vue';

const model = ref([
    {
        label: 'Home',
        items: [
            {
                label: 'Dashboard',
                icon: 'pi pi-fw pi-home',
                to: '/'
            }
        ]
    },
    {
        label: 'Security',
        items: [
            {
                label: 'Threats',
                icon: 'pi pi-fw pi-shield',
                to: '/threats'
            },
            {
                label: 'Alerts',
                icon: 'pi pi-fw pi-bell',
                to: '/alerts'
            },
            {
                label: 'Audit Logs',
                icon: 'pi pi-fw pi-list',
                to: '/logs'
            }
        ]
    },
    {
        label: 'Activity',
        items: [
            {
                label: 'Attendance',
                icon: 'pi pi-fw pi-clock',
                to: '/attendance'
            },
            {
                label: 'QR Codes',
                icon: 'pi pi-fw pi-qrcode',
                to: '/qrcodes'
            },
            {
                label: 'Scan',
                icon: 'pi pi-fw pi-camera',
                to: '/scan'
            }
        ]
    },
    {
        label: 'Administration',
        items: [
            {
                label: 'Company',
                icon: 'pi pi-fw pi-building',
                to: '/company'
            },
            {
                label: 'Branches',
                icon: 'pi pi-fw pi-map-marker',
                to: '/branches'
            },
            {
                label: 'Roster',
                icon: 'pi pi-fw pi-calendar',
                to: '/roster'
            },
            {
                label: 'Users',
                icon: 'pi pi-fw pi-users',
                to: '/users'
            },
            {
                label: 'Settings',
                icon: 'pi pi-fw pi-cog',
                to: '/settings'
            }
        ]
    }
]);
</script>

<template>
    <ul class="layout-menu">
        <template v-for="(item, i) in model" :key="item">
            <app-menu-item v-if="!item.separator" :item="item" :index="i"></app-menu-item>
            <li v-if="item.separator" class="menu-separator"></li>
        </template>
    </ul>
</template>

<style lang="scss" scoped></style>
