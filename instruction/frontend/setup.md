# Frontend Setup Guide — SecuritySoftware

## Overview

The frontend is a **Vue 3** single-page application built on the **Sakai-Vue** admin template by PrimeFaces. It provides a security-focused dashboard with sidebar navigation, topbar, and body content area.

### Tech Stack

| Technology | Version | Purpose |
|---|---|---|
| **Vue 3** | ^3.4.34 | UI framework |
| **PrimeVue** | ^4.5.4 | Component library (80+ components) |
| **Tailwind CSS** | ^4.1.17 | Utility-first CSS framework |
| **Vite** | ^5.3.1 | Build tool & dev server |
| **Pinia** | latest | State management |
| **Axios** | latest | HTTP client |
| **Vue Router** | ^4.4.0 | Client-side routing |
| **PrimeIcons** | ^7.0.0 | Icon library |
| **@primeuix/themes** | ^2.0.0 | Theme presets (Aura) |

---

## Quick Start

```bash
cd frontend
npm install
npm run dev
```

The dev server starts at **http://localhost:5173**.

---

## Project Structure

```
frontend/
├── .env                        # Environment variables (VITE_API_URL, VITE_APP_NAME)
├── .env.example                # Template for .env
├── index.html                  # HTML entry point
├── package.json                # Dependencies & scripts
├── vite.config.mjs             # Vite configuration
│
├── public/                     # Static assets (favicon, etc.)
│
└── src/
    ├── App.vue                 # Root component (<router-view />)
    ├── main.js                 # App bootstrap (Vue, Pinia, Router, PrimeVue)
    │
    ├── assets/                 # SCSS & Tailwind styles
    │   ├── tailwind.css        # Tailwind entry point
    │   ├── styles.scss         # Global styles
    │   ├── layout/             # Layout-specific SCSS
    │   └── demo/               # Demo styles (can be cleaned up)
    │
    ├── router/
    │   └── index.js            # Route definitions + auth navigation guard
    │
    ├── stores/                 # Pinia stores
    │   └── auth.js             # Auth store (login, logout, token management)
    │
    ├── services/               # API layer
    │   └── api.js              # Axios instance with JWT interceptors
    │
    ├── layout/                 # App shell (DO NOT DELETE)
    │   ├── AppLayout.vue       # Main wrapper (Topbar + Sidebar + Content + Footer)
    │   ├── AppTopbar.vue       # Top bar with logo, dark mode, user actions
    │   ├── AppSidebar.vue      # Sidebar container
    │   ├── AppMenu.vue         # Navigation menu definition
    │   ├── AppMenuItem.vue     # Recursive menu item renderer
    │   ├── AppFooter.vue       # Footer bar
    │   ├── AppConfigurator.vue # Theme/color picker drawer
    │   └── composables/
    │       └── layout.js       # useLayout() composable for layout state
    │
    └── views/                  # Page components
        ├── Dashboard.vue       # Security dashboard (stats, alerts, threats)
        ├── Threats.vue         # Threat management table
        ├── Alerts.vue          # Security alerts list
        ├── AuditLogs.vue       # Activity/audit log viewer
        ├── Users.vue           # User management
        ├── Settings.vue        # Application settings
        └── pages/
            ├── NotFound.vue    # 404 page
            └── auth/
                ├── Login.vue   # Login page (JWT auth)
                ├── Access.vue  # 403 Access Denied
                └── Error.vue   # Error page
```

---

## Architecture

### Routing & Auth Guard

Routes are defined in `src/router/index.js` with two tiers:

1. **Layout-wrapped routes** — Children of `/` with `AppLayout` as the component. These render inside the sidebar/topbar shell. All have `meta: { requiresAuth: true }`.
2. **Standalone routes** — Top-level routes for Login, Access Denied, Error, and 404 that render full-page without the layout shell.

A `beforeEach` navigation guard checks `auth.isAuthenticated` and redirects unauthenticated users to `/auth/login`. Authenticated users are redirected away from the login page to `/`.

### Routes

| Path | Name | Component | Auth Required | Layout |
|---|---|---|---|---|
| `/` | dashboard | Dashboard.vue | ✅ | AppLayout |
| `/threats` | threats | Threats.vue | ✅ | AppLayout |
| `/alerts` | alerts | Alerts.vue | ✅ | AppLayout |
| `/logs` | logs | AuditLogs.vue | ✅ | AppLayout |
| `/users` | users | Users.vue | ✅ | AppLayout |
| `/settings` | settings | Settings.vue | ✅ | AppLayout |
| `/auth/login` | login | Login.vue | ❌ | Standalone |
| `/auth/access` | accessDenied | Access.vue | ❌ | Standalone |
| `/auth/error` | error | Error.vue | ❌ | Standalone |
| `/:pathMatch(.*)*` | notfound | NotFound.vue | ❌ | Standalone |

### State Management (Pinia)

**Auth Store** (`src/stores/auth.js`):

| Property / Method | Type | Description |
|---|---|---|
| `user` | `ref` | Current user object |
| `token` | `ref` | JWT access token (persisted in localStorage) |
| `refreshToken` | `ref` | JWT refresh token (persisted in localStorage) |
| `loading` | `ref` | Loading state for auth operations |
| `error` | `ref` | Last error message |
| `isAuthenticated` | `computed` | `true` if token exists |
| `userFullName` | `computed` | User's full name |
| `login(credentials)` | `action` | POST to `/auth/login`, stores tokens |
| `logout()` | `action` | Clears tokens, redirects to login |
| `fetchUser()` | `action` | GET `/auth/me`, updates user |
| `refreshAccessToken()` | `action` | POST `/auth/refresh`, updates access token |

### API Layer (Axios)

`src/services/api.js` exports a pre-configured Axios instance:

- **Base URL**: From `VITE_API_URL` env variable (default: `http://localhost:8000/api`)
- **Request Interceptor**: Attaches `Authorization: Bearer <token>` header
- **Response Interceptor**: On 401, attempts token refresh. If refresh fails, clears auth and redirects to login.

**Usage in components/stores:**
```js
import api from '@/services/api';

// GET
const { data } = await api.get('/threats');

// POST
const { data } = await api.post('/alerts', payload);
```

### Layout System

The layout is managed by `src/layout/composables/layout.js` — a module-scoped reactive composable (NOT Pinia). It controls:

- **Menu mode**: `static` (always visible) or `overlay` (hamburger toggle)
- **Dark mode**: Toggle via `.app-dark` CSS class
- **Mobile breakpoint**: 991px
- **Config sidebar**: Theme/color picker

### Sidebar Menu

Menu items are defined in `src/layout/AppMenu.vue` as a `ref` array. Each item has:

```js
{ label: 'Dashboard', icon: 'pi pi-fw pi-home', to: '/' }
```

Current navigation structure:
- **Home** → Dashboard
- **Security** → Threats, Alerts, Audit Logs
- **Administration** → Users, Settings

To add a new page:
1. Create the view in `src/views/`
2. Add the route in `src/router/index.js` (as a child of the AppLayout route)
3. Add the menu item in `src/layout/AppMenu.vue`

### PrimeVue Auto-Import

PrimeVue components are **auto-imported** via `unplugin-vue-components` with `PrimeVueResolver`. You do NOT need to manually import components like `<Button>`, `<DataTable>`, `<InputText>`, etc. — just use them directly in templates.

### Theming

- **Preset**: Aura (from `@primeuix/themes`)
- **Dark mode**: CSS class `.app-dark` on `<html>` element
- **Primary color**: Configurable via AppConfigurator drawer (palette picker)
- **Surface colors**: Configurable via AppConfigurator
- **Custom styles**: `src/assets/styles.scss` and `src/assets/layout/`

---

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `VITE_API_URL` | `http://localhost:8000/api` | Backend API base URL |
| `VITE_APP_NAME` | `SecuritySoftware` | Application display name |

Copy `.env.example` to `.env` and adjust as needed.

---

## NPM Scripts

| Command | Description |
|---|---|
| `npm run dev` | Start Vite dev server (hot reload) |
| `npm run build` | Build for production → `dist/` |
| `npm run preview` | Preview production build locally |
| `npm run lint` | Run ESLint with auto-fix |

---

## Adding New Features

### Adding a New Page

1. **Create the view**: `src/views/MyPage.vue`
2. **Add the route** in `src/router/index.js`:
   ```js
   {
       path: '/my-page',
       name: 'myPage',
       component: () => import('@/views/MyPage.vue')
   }
   ```
3. **Add the menu item** in `src/layout/AppMenu.vue`:
   ```js
   { label: 'My Page', icon: 'pi pi-fw pi-star', to: '/my-page' }
   ```

### Adding a New Pinia Store

1. Create `src/stores/myStore.js`:
   ```js
   import { defineStore } from 'pinia';
   import { ref, computed } from 'vue';
   import api from '@/services/api';

   export const useMyStore = defineStore('myStore', () => {
       const items = ref([]);
       const loading = ref(false);

       async function fetchItems() {
           loading.value = true;
           try {
               const { data } = await api.get('/my-endpoint');
               items.value = data;
           } finally {
               loading.value = false;
           }
       }

       return { items, loading, fetchItems };
   });
   ```

2. Use in a component:
   ```vue
   <script setup>
   import { useMyStore } from '@/stores/myStore';
   const store = useMyStore();
   store.fetchItems();
   </script>
   ```

### Adding API Endpoints

All API calls go through `src/services/api.js`. For service-specific logic, create files in `src/services/`:

```js
// src/services/threatService.js
import api from './api';

export const threatService = {
    getAll: () => api.get('/threats'),
    getById: (id) => api.get(`/threats/${id}`),
    create: (data) => api.post('/threats', data),
    update: (id, data) => api.put(`/threats/${id}`, data),
    delete: (id) => api.delete(`/threats/${id}`)
};
```

---

## Backend API Contract

The frontend expects the following API endpoints from the backend:

### Auth Endpoints

| Method | Path | Request Body | Response |
|---|---|---|---|
| POST | `/auth/login` | `{ email, password }` | `{ access_token, refresh_token, user }` |
| POST | `/auth/refresh` | `{ refresh_token }` | `{ access_token }` |
| GET | `/auth/me` | — | `{ id, email, first_name, last_name, role }` |

### Data Endpoints (to be implemented)

| Method | Path | Description |
|---|---|---|
| GET | `/threats` | List all threats |
| GET | `/alerts` | List all alerts |
| GET | `/logs` | List audit logs |
| GET | `/users` | List users |
| PUT | `/settings` | Update settings |

---

## Notes

- The frontend currently uses **mock/static data** in all views. Once the backend is ready, replace static data with API calls via the `api` service.
- PrimeVue components are auto-imported — no manual imports needed in `<template>`.
- The `src/layout/` directory is the Sakai template shell — modify with care to preserve sidebar/topbar/footer behavior.
- Token persistence uses `localStorage`. For production security software, consider migrating to `httpOnly` cookies set by the backend.
