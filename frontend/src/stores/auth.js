import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import api from '@/services/api';
import router from '@/router';

export const useAuthStore = defineStore('auth', () => {
    const user = ref(null);
    const token = ref(localStorage.getItem('token'));
    const refreshToken = ref(localStorage.getItem('refreshToken'));
    const loading = ref(false);
    const error = ref(null);

    const isAuthenticated = computed(() => !!token.value);
    const userFullName = computed(() => (user.value ? `${user.value.first_name} ${user.value.last_name}` : ''));

    async function login(credentials) {
        loading.value = true;
        error.value = null;
        try {
            const { data } = await api.post('/auth/token/', credentials);
            token.value = data.access;
            refreshToken.value = data.refresh;
            localStorage.setItem('token', data.access);
            localStorage.setItem('refreshToken', data.refresh);
            await fetchUser();
            return data;
        } catch (err) {
            error.value = err.response?.data?.detail || 'Login failed. Please try again.';
            throw err;
        } finally {
            loading.value = false;
        }
    }

    function logout() {
        token.value = null;
        refreshToken.value = null;
        user.value = null;
        error.value = null;
        localStorage.removeItem('token');
        localStorage.removeItem('refreshToken');
        router.push({ name: 'login' });
    }

    async function fetchUser() {
        if (!token.value) return;
        loading.value = true;
        try {
            const { data } = await api.get('/auth/me/');
            user.value = data;
        } catch {
            logout();
        } finally {
            loading.value = false;
        }
    }

    async function refreshAccessToken() {
        try {
            const { data } = await api.post('/auth/token/refresh/', {
                refresh: refreshToken.value
            });
            token.value = data.access;
            localStorage.setItem('token', data.access);
            return data.access;
        } catch {
            logout();
            return null;
        }
    }

    return {
        user,
        token,
        refreshToken,
        loading,
        error,
        isAuthenticated,
        userFullName,
        login,
        logout,
        fetchUser,
        refreshAccessToken
    };
});
