<script setup>
import { useGooglePlaces } from '@/composables/useGooglePlaces';

const props = defineProps({
    modelValue: {
        type: Object,
        required: true
    },
    submitted: {
        type: Boolean,
        default: false
    },
    label: {
        type: String,
        default: 'Address *'
    },
    requireStreet: {
        type: Boolean,
        default: true
    }
});

const emit = defineEmits(['update:modelValue']);

const { suggestions, loading: searchingAddress, search: searchPlaces, getPlaceDetails } = useGooglePlaces();

const updateField = (field, value) => {
    emit('update:modelValue', { ...props.modelValue, [field]: value });
};

const searchAddress = (event) => {
    searchPlaces(event.query);
};

const onAddressSelect = async (event) => {
    const selected = event.value;
    if (selected && selected.placeId) {
        const details = await getPlaceDetails(selected.placeId);
        if (details) {
            emit('update:modelValue', { ...details });
        }
    }
};
</script>

<template>
    <div class="flex flex-col gap-4">
        <label class="font-medium">{{ label }}</label>
        <AutoComplete
            :modelValue="modelValue.full"
            @update:modelValue="updateField('full', $event)"
            :suggestions="suggestions"
            optionLabel="full"
            placeholder="Search address from Google..."
            @complete="searchAddress"
            @item-select="onAddressSelect"
            :forceSelection="false"
            :loading="searchingAddress"
            class="w-full"
        />
        <small class="text-muted-color -mt-2"><i class="pi pi-map-marker mr-1"></i>Select from Google Places or fill manually below</small>

        <div class="grid grid-cols-2 gap-4">
            <div class="flex flex-col gap-2">
                <label class="text-sm">Flat / House No.</label>
                <InputText :modelValue="modelValue.flat" @update:modelValue="updateField('flat', $event)" placeholder="Flat / House No." />
            </div>
            <div class="flex flex-col gap-2">
                <label class="text-sm">Street <span v-if="requireStreet">*</span></label>
                <InputText :modelValue="modelValue.street" @update:modelValue="updateField('street', $event)" :invalid="submitted && requireStreet && !modelValue.street?.trim()" placeholder="Street" />
                <small v-if="submitted && requireStreet && !modelValue.street?.trim()" class="text-red-500">Street is required.</small>
            </div>
        </div>
        <div class="grid grid-cols-2 gap-4">
            <div class="flex flex-col gap-2">
                <label class="text-sm">Suburb</label>
                <InputText :modelValue="modelValue.suburb" @update:modelValue="updateField('suburb', $event)" placeholder="Suburb" />
            </div>
            <div class="flex flex-col gap-2">
                <label class="text-sm">Postal Code</label>
                <InputText :modelValue="modelValue.postalCode" @update:modelValue="updateField('postalCode', $event)" placeholder="Postal Code" />
            </div>
        </div>
        <div class="grid grid-cols-2 gap-4">
            <div class="flex flex-col gap-2">
                <label class="text-sm">State</label>
                <InputText :modelValue="modelValue.state" @update:modelValue="updateField('state', $event)" placeholder="State" />
            </div>
            <div class="flex flex-col gap-2">
                <label class="text-sm">Country</label>
                <InputText :modelValue="modelValue.country" @update:modelValue="updateField('country', $event)" placeholder="Country" />
            </div>
        </div>
    </div>
</template>
