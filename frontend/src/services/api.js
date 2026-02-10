import axios from 'axios';

const api = axios.create({
    baseURL: import.meta.env.VITE_API_URL,
    headers: {
        'Content-Type': 'application/json'
    }
});

// Request interceptor — attach JWT token
api.interceptors.request.use(
    (config) => {
        const token = localStorage.getItem('token');
        if (token) {
            config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
    },
    (error) => Promise.reject(error)
);

// Response interceptor — handle 401 and token refresh
api.interceptors.response.use(
    (response) => response,
    async (error) => {
        const originalRequest = error.config;

        if (error.response?.status === 401 && !originalRequest._retry) {
            originalRequest._retry = true;

            const refreshTokenValue = localStorage.getItem('refreshToken');
            if (refreshTokenValue) {
                try {
                    const { data } = await axios.post(
                        `${import.meta.env.VITE_API_URL}/auth/token/refresh/`,
                        { refresh: refreshTokenValue },
                        { headers: { 'Content-Type': 'application/json' } }
                    );

                    localStorage.setItem('token', data.access);
                    originalRequest.headers.Authorization = `Bearer ${data.access}`;
                    return api(originalRequest);
                } catch {
                    // Refresh failed — clear auth and redirect to login
                    localStorage.removeItem('token');
                    localStorage.removeItem('refreshToken');
                    window.location.href = '/auth/login';
                }
            } else {
                localStorage.removeItem('token');
                window.location.href = '/auth/login';
            }
        }

        return Promise.reject(error);
    }
);

export default api;
