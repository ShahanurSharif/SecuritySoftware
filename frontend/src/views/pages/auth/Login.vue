<script setup>
import { ref } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import { useAuthStore } from '@/stores/auth';
import { useToast } from 'primevue/usetoast';

const router = useRouter();
const route = useRoute();
const auth = useAuthStore();
const toast = useToast();

const username = ref('');
const password = ref('');
const checked = ref(false);
const submitting = ref(false);

const handleLogin = async () => {
    if (!username.value || !password.value) {
        toast.add({ severity: 'warn', summary: 'Validation', detail: 'Please enter username and password.', life: 3000 });
        return;
    }
    submitting.value = true;
    try {
        await auth.login({ username: username.value, password: password.value });
        const redirect = route.query.redirect || '/';
        router.push(redirect);
    } catch (err) {
        toast.add({ severity: 'error', summary: 'Login Failed', detail: auth.error || 'Invalid credentials.', life: 5000 });
    } finally {
        submitting.value = false;
    }
};
</script>

<template>
    <Toast />
    <div class="bg-surface-50 dark:bg-surface-950 flex items-center justify-center min-h-screen min-w-[100vw] overflow-hidden">
        <div class="flex flex-col items-center justify-center">
            <div style="border-radius: 56px; padding: 0.3rem; background: linear-gradient(180deg, var(--primary-color) 10%, rgba(33, 150, 243, 0) 30%)">
                <div class="w-full bg-surface-0 dark:bg-surface-900 py-20 px-8 sm:px-20" style="border-radius: 53px">
                    <div class="text-center mb-8">
                        <div class="mb-8 flex justify-center">
                            <div class="flex items-center justify-center bg-primary rounded-full" style="width: 4rem; height: 4rem">
                                <i class="pi pi-shield text-3xl text-white"></i>
                            </div>
                        </div>
                        <div class="text-surface-900 dark:text-surface-0 text-3xl font-medium mb-4">SecuritySoftware</div>
                        <span class="text-muted-color font-medium">Sign in to continue</span>
                    </div>

                    <form @submit.prevent="handleLogin">
                        <label for="username1" class="block text-surface-900 dark:text-surface-0 text-xl font-medium mb-2">Username</label>
                        <InputText id="username1" type="text" placeholder="Username" class="w-full md:w-[30rem] mb-8" v-model="username" />

                        <label for="password1" class="block text-surface-900 dark:text-surface-0 font-medium text-xl mb-2">Password</label>
                        <Password id="password1" v-model="password" placeholder="Password" :toggleMask="true" class="mb-4" fluid :feedback="false"></Password>

                        <div class="flex items-center justify-between mt-2 mb-8 gap-8">
                            <div class="flex items-center">
                                <Checkbox v-model="checked" id="rememberme1" binary class="mr-2"></Checkbox>
                                <label for="rememberme1">Remember me</label>
                            </div>
                            <span class="font-medium no-underline ml-2 text-right cursor-pointer text-primary">Forgot password?</span>
                        </div>
                        <Button type="submit" label="Sign In" class="w-full" :loading="submitting"></Button>
                    </form>
                </div>
            </div>
        </div>
    </div>
</template>

<style scoped>
.pi-eye {
    transform: scale(1.6);
    margin-right: 1rem;
}

.pi-eye-slash {
    transform: scale(1.6);
    margin-right: 1rem;
}
</style>
