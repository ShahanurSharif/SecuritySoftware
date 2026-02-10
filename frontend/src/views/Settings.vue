<script setup>
import { ref } from 'vue';
import { useToast } from 'primevue/usetoast';

const toast = useToast();

const generalSettings = ref({
    appName: 'SecuritySoftware',
    sessionTimeout: 30,
    maxLoginAttempts: 5,
    enableNotifications: true,
    enableAuditLog: true,
    maintenanceMode: false
});

const notificationSettings = ref({
    emailAlerts: true,
    criticalOnly: false,
    dailyDigest: true,
    alertEmail: 'admin@security.io'
});

const saveGeneral = () => {
    toast.add({ severity: 'success', summary: 'Saved', detail: 'General settings updated successfully.', life: 3000 });
};

const saveNotifications = () => {
    toast.add({ severity: 'success', summary: 'Saved', detail: 'Notification settings updated successfully.', life: 3000 });
};
</script>

<template>
    <Toast />
    <div class="grid grid-cols-12 gap-8">
        <!-- General Settings -->
        <div class="col-span-12 lg:col-span-6">
            <div class="card">
                <div class="font-semibold text-xl mb-4">General Settings</div>
                <div class="flex flex-col gap-6">
                    <div class="flex flex-col gap-2">
                        <label for="appName" class="font-medium">Application Name</label>
                        <InputText id="appName" v-model="generalSettings.appName" />
                    </div>
                    <div class="flex flex-col gap-2">
                        <label for="sessionTimeout" class="font-medium">Session Timeout (minutes)</label>
                        <InputNumber id="sessionTimeout" v-model="generalSettings.sessionTimeout" :min="5" :max="120" />
                    </div>
                    <div class="flex flex-col gap-2">
                        <label for="maxAttempts" class="font-medium">Max Login Attempts</label>
                        <InputNumber id="maxAttempts" v-model="generalSettings.maxLoginAttempts" :min="3" :max="10" />
                    </div>
                    <div class="flex items-center gap-2">
                        <ToggleSwitch v-model="generalSettings.enableNotifications" />
                        <label class="font-medium">Enable Notifications</label>
                    </div>
                    <div class="flex items-center gap-2">
                        <ToggleSwitch v-model="generalSettings.enableAuditLog" />
                        <label class="font-medium">Enable Audit Logging</label>
                    </div>
                    <div class="flex items-center gap-2">
                        <ToggleSwitch v-model="generalSettings.maintenanceMode" />
                        <label class="font-medium">Maintenance Mode</label>
                    </div>
                    <Button label="Save Settings" icon="pi pi-save" @click="saveGeneral" />
                </div>
            </div>
        </div>

        <!-- Notification Settings -->
        <div class="col-span-12 lg:col-span-6">
            <div class="card">
                <div class="font-semibold text-xl mb-4">Notification Settings</div>
                <div class="flex flex-col gap-6">
                    <div class="flex flex-col gap-2">
                        <label for="alertEmail" class="font-medium">Alert Email</label>
                        <InputText id="alertEmail" v-model="notificationSettings.alertEmail" />
                    </div>
                    <div class="flex items-center gap-2">
                        <ToggleSwitch v-model="notificationSettings.emailAlerts" />
                        <label class="font-medium">Email Alerts</label>
                    </div>
                    <div class="flex items-center gap-2">
                        <ToggleSwitch v-model="notificationSettings.criticalOnly" />
                        <label class="font-medium">Critical Alerts Only</label>
                    </div>
                    <div class="flex items-center gap-2">
                        <ToggleSwitch v-model="notificationSettings.dailyDigest" />
                        <label class="font-medium">Daily Digest</label>
                    </div>
                    <Button label="Save Notifications" icon="pi pi-save" @click="saveNotifications" />
                </div>
            </div>
        </div>
    </div>
</template>
