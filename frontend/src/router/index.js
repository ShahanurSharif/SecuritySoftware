import AppLayout from '@/layout/AppLayout.vue';
import { createRouter, createWebHistory } from 'vue-router';
import { useAuthStore } from '@/stores/auth';

const router = createRouter({
    history: createWebHistory(),
    routes: [
        {
            path: '/',
            component: AppLayout,
            meta: { requiresAuth: true },
            children: [
                {
                    path: '/',
                    name: 'dashboard',
                    component: () => import('@/views/Dashboard.vue')
                },
                {
                    path: '/threats',
                    name: 'threats',
                    component: () => import('@/views/Threats.vue')
                },
                {
                    path: '/alerts',
                    name: 'alerts',
                    component: () => import('@/views/Alerts.vue')
                },
                {
                    path: '/logs',
                    name: 'logs',
                    component: () => import('@/views/AuditLogs.vue')
                },
                {
                    path: '/users',
                    name: 'users',
                    component: () => import('@/views/Users.vue')
                },
                {
                    path: '/company',
                    name: 'company',
                    component: () => import('@/views/Company.vue')
                },
                {
                    path: '/branches',
                    name: 'branches',
                    component: () => import('@/views/Branches.vue')
                },
                {
                    path: '/settings',
                    name: 'settings',
                    component: () => import('@/views/Settings.vue')
                },
                {
                    path: '/attendance',
                    name: 'attendance',
                    component: () => import('@/views/Attendance.vue')
                },
                {
                    path: '/qrcodes',
                    name: 'qrcodes',
                    component: () => import('@/views/QRCodes.vue')
                },
                {
                    path: '/scan',
                    name: 'scan',
                    component: () => import('@/views/Scan.vue')
                }
            ]
        },
        {
            path: '/auth/login',
            name: 'login',
            component: () => import('@/views/pages/auth/Login.vue')
        },
        {
            path: '/auth/access',
            name: 'accessDenied',
            component: () => import('@/views/pages/auth/Access.vue')
        },
        {
            path: '/auth/error',
            name: 'error',
            component: () => import('@/views/pages/auth/Error.vue')
        },
        {
            path: '/:pathMatch(.*)*',
            name: 'notfound',
            component: () => import('@/views/pages/NotFound.vue')
        }
    ]
});

// Navigation guard — protect routes that require auth
const publicRouteNames = ['login', 'accessDenied', 'error', 'notfound'];

router.beforeEach((to, from, next) => {
    const auth = useAuthStore();

    if (to.meta.requiresAuth && !auth.isAuthenticated) {
        next({ name: 'login', query: { redirect: to.fullPath } });
    } else if (to.name === 'login' && auth.isAuthenticated) {
        next({ path: '/' });
    } else {
        next();
    }
});

export default router;
