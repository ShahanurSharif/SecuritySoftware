<script setup>
import { ref, onMounted } from 'vue';
import { useToast } from 'primevue/usetoast';
import api from '@/services/api';

const props = defineProps({
    branches: Array,
    isAdmin: Boolean
});

const emit = defineEmits(['templates-updated']);
const toast = useToast();

// ─── State ─────────────────────────────────────────────────────
const templates = ref([]);
const templatesLoading = ref(false);
const templateDialog = ref(false);
const deleteTemplateDialog = ref(false);
const templateSubmitted = ref(false);
const isEditingTemplate = ref(false);
const selectedTemplate = ref(null);

const emptyTemplate = { id: null, name: '', start_time: '', end_time: '', branch: null, color: '#3B82F6', hourly_rate: 0, break_duration_minutes: 0, is_active: true };
const templateForm = ref({ ...emptyTemplate });

// ─── Fetch ─────────────────────────────────────────────────────
const fetchAllTemplates = async () => {
    templatesLoading.value = true;
    try {
        const { data } = await api.get('/roster/shift-templates/', { params: { page_size: 1000 } });
        templates.value = data.results || data;
    } catch {
        toast.add({ severity: 'error', summary: 'Error', detail: 'Failed to load templates.', life: 4000 });
    } finally {
        templatesLoading.value = false;
    }
};

// ─── CRUD ──────────────────────────────────────────────────────
const openNewTemplate = () => {
    templateForm.value = { ...emptyTemplate };
    isEditingTemplate.value = false;
    templateSubmitted.value = false;
    templateDialog.value = true;
};

const editTemplate = (t) => {
    templateForm.value = {
        id: t.id, name: t.name, start_time: t.start_time?.slice(0, 5) || '', end_time: t.end_time?.slice(0, 5) || '',
        branch: t.branch, color: t.color, hourly_rate: t.hourly_rate || 0, break_duration_minutes: t.break_duration_minutes || 0, is_active: t.is_active
    };
    isEditingTemplate.value = true;
    templateSubmitted.value = false;
    templateDialog.value = true;
};

const saveTemplate = async () => {
    templateSubmitted.value = true;
    if (!templateForm.value.name || !templateForm.value.branch || !templateForm.value.start_time || !templateForm.value.end_time) return;
    try {
        const payload = { ...templateForm.value };
        if (isEditingTemplate.value) {
            await api.put(`/roster/shift-templates/${templateForm.value.id}/`, payload);
            toast.add({ severity: 'success', summary: 'Updated', detail: 'Template updated.', life: 3000 });
        } else {
            await api.post('/roster/shift-templates/', payload);
            toast.add({ severity: 'success', summary: 'Created', detail: 'Template created.', life: 3000 });
        }
        templateDialog.value = false;
        fetchAllTemplates();
        emit('templates-updated');
    } catch (err) {
        const detail = err.response?.data?.name?.[0] || err.response?.data?.detail || 'Save failed.';
        toast.add({ severity: 'error', summary: 'Error', detail, life: 5000 });
    }
};

const confirmDeleteTemplate = (t) => { selectedTemplate.value = t; deleteTemplateDialog.value = true; };
const deleteTemplate = async () => {
    try {
        await api.delete(`/roster/shift-templates/${selectedTemplate.value.id}/`);
        toast.add({ severity: 'success', summary: 'Deleted', detail: 'Template deleted.', life: 3000 });
        deleteTemplateDialog.value = false;
        fetchAllTemplates();
        emit('templates-updated');
    } catch {
        toast.add({ severity: 'error', summary: 'Error', detail: 'Delete failed.', life: 4000 });
    }
};

const refresh = () => fetchAllTemplates();
defineExpose({ refresh });

onMounted(fetchAllTemplates);
</script>

<template>
    <div class="card">
        <div class="flex justify-between items-center mb-4">
            <span class="font-semibold text-lg">Shift Templates</span>
            <Button v-if="isAdmin" label="New Template" icon="pi pi-plus" @click="openNewTemplate" />
        </div>

        <DataTable :value="templates" :loading="templatesLoading" stripedRows size="small">
            <Column field="name" header="Name" sortable />
            <Column field="branch_name" header="Branch" sortable />
            <Column field="start_time" header="Start" sortable>
                <template #body="{ data }">{{ data.start_time?.slice(0, 5) }}</template>
            </Column>
            <Column field="end_time" header="End">
                <template #body="{ data }">{{ data.end_time?.slice(0, 5) }}</template>
            </Column>
            <Column field="color" header="Color" style="min-width: 4rem">
                <template #body="{ data }"><div class="w-6 h-6 rounded" :style="{ backgroundColor: data.color }"></div></template>
            </Column>
            <Column field="net_hours" header="Net Hours" sortable style="min-width: 5rem">
                <template #body="{ data }"><span class="font-semibold">{{ data.net_hours }}h</span></template>
            </Column>
            <Column field="hourly_rate" header="Rate" style="min-width: 5rem">
                <template #body="{ data }">
                    <span v-if="data.hourly_rate > 0">${{ Number(data.hourly_rate).toFixed(2) }}/h</span>
                    <span v-else class="text-muted-color">—</span>
                </template>
            </Column>
            <Column field="break_duration_minutes" header="Break" style="min-width: 4rem">
                <template #body="{ data }">{{ data.break_duration_minutes }}min</template>
            </Column>
            <Column field="is_active" header="Active">
                <template #body="{ data }"><Tag :value="data.is_active ? 'Active' : 'Inactive'" :severity="data.is_active ? 'success' : 'secondary'" /></template>
            </Column>
            <Column v-if="isAdmin" header="Actions" style="min-width: 8rem">
                <template #body="{ data }">
                    <div class="flex gap-1">
                        <Button icon="pi pi-pencil" text rounded severity="info" @click="editTemplate(data)" />
                        <Button icon="pi pi-trash" text rounded severity="danger" @click="confirmDeleteTemplate(data)" />
                    </div>
                </template>
            </Column>
            <template #empty>No templates found.</template>
        </DataTable>
    </div>

    <!-- Template Dialog -->
    <Dialog v-model:visible="templateDialog" :header="isEditingTemplate ? 'Edit Template' : 'New Template'" modal style="width: 28rem">
        <div class="flex flex-col gap-4">
            <div class="flex flex-col gap-1">
                <label class="font-semibold text-sm">Name *</label>
                <InputText v-model="templateForm.name" :class="{ 'p-invalid': templateSubmitted && !templateForm.name }" />
            </div>
            <div class="flex flex-col gap-1">
                <label class="font-semibold text-sm">Branch *</label>
                <Select v-model="templateForm.branch" :options="branches" optionLabel="label" optionValue="value" placeholder="Select Branch" :class="{ 'p-invalid': templateSubmitted && !templateForm.branch }" filter />
            </div>
            <div class="grid grid-cols-2 gap-3">
                <div class="flex flex-col gap-1">
                    <label class="font-semibold text-sm">Start Time *</label>
                    <InputMask v-model="templateForm.start_time" mask="99:99" placeholder="HH:MM" :class="{ 'p-invalid': templateSubmitted && !templateForm.start_time }" />
                </div>
                <div class="flex flex-col gap-1">
                    <label class="font-semibold text-sm">End Time *</label>
                    <InputMask v-model="templateForm.end_time" mask="99:99" placeholder="HH:MM" :class="{ 'p-invalid': templateSubmitted && !templateForm.end_time }" />
                </div>
            </div>
            <div class="grid grid-cols-2 gap-3">
                <div class="flex flex-col gap-1">
                    <label class="font-semibold text-sm">Hourly Rate ($)</label>
                    <InputNumber v-model="templateForm.hourly_rate" mode="currency" currency="USD" :minFractionDigits="2" :min="0" />
                </div>
                <div class="flex flex-col gap-1">
                    <label class="font-semibold text-sm">Break (minutes)</label>
                    <InputNumber v-model="templateForm.break_duration_minutes" :min="0" suffix=" min" />
                </div>
            </div>
            <div class="flex flex-col gap-1">
                <label class="font-semibold text-sm">Color</label>
                <ColorPicker v-model="templateForm.color" />
            </div>
            <div class="flex items-center gap-2">
                <ToggleSwitch v-model="templateForm.is_active" />
                <label class="text-sm">Active</label>
            </div>
        </div>
        <template #footer>
            <Button label="Cancel" text @click="templateDialog = false" />
            <Button :label="isEditingTemplate ? 'Update' : 'Create'" icon="pi pi-check" @click="saveTemplate" />
        </template>
    </Dialog>

    <!-- Delete Template -->
    <Dialog v-model:visible="deleteTemplateDialog" header="Confirm Delete" modal style="width: 24rem">
        <p>Delete this template?</p>
        <template #footer>
            <Button label="Cancel" text @click="deleteTemplateDialog = false" />
            <Button label="Delete" icon="pi pi-trash" severity="danger" @click="deleteTemplate" />
        </template>
    </Dialog>
</template>
