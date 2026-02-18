import { ref } from 'vue';

const GOOGLE_API_KEY = import.meta.env.VITE_GOOGLE_PLACES_API_KEY || '';

/**
 * Composable for Google Places Autocomplete.
 * Uses the Places API (New) — Autocomplete + Place Details via REST.
 */
export function useGooglePlaces() {
    const suggestions = ref([]);
    const loading = ref(false);

    let abortController = null;

    /**
     * Search for address suggestions.
     * @param {string} query — user input text
     */
    const search = async (query) => {
        if (!query || query.length < 3) {
            suggestions.value = [];
            return;
        }

        // Cancel any in-flight request
        if (abortController) abortController.abort();
        abortController = new AbortController();

        loading.value = true;

        try {
            const res = await fetch('https://places.googleapis.com/v1/places:autocomplete', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Goog-Api-Key': GOOGLE_API_KEY
                },
                body: JSON.stringify({
                    input: query,
                    includedPrimaryTypes: ['street_address', 'subpremise', 'premise', 'route', 'locality'],
                    languageCode: 'en'
                }),
                signal: abortController.signal
            });

            const json = await res.json();
            const items = json.suggestions || [];

            suggestions.value = items
                .filter((s) => s.placePrediction)
                .map((s) => ({
                    placeId: s.placePrediction.placeId,
                    full: s.placePrediction.text?.text || '',
                    structuredFormat: s.placePrediction.structuredFormat || {}
                }));
        } catch (err) {
            if (err.name !== 'AbortError') {
                console.error('Google Places autocomplete error:', err);
                suggestions.value = [];
            }
        } finally {
            loading.value = false;
        }
    };

    /**
     * Fetch full Place Details and extract address components.
     * @param {string} placeId — Google Place ID
     * @returns {{ full, flat, street, suburb, postalCode, state, country }}
     */
    const getPlaceDetails = async (placeId) => {
        try {
            const res = await fetch(`https://places.googleapis.com/v1/places/${placeId}`, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Goog-Api-Key': GOOGLE_API_KEY,
                    'X-Goog-FieldMask': 'formattedAddress,addressComponents'
                }
            });

            const place = await res.json();
            return parseAddressComponents(place);
        } catch (err) {
            console.error('Google Place Details error:', err);
            return null;
        }
    };

    /**
     * Parse addressComponents from Place Details into our flat structure.
     */
    const parseAddressComponents = (place) => {
        const components = place.addressComponents || [];
        const get = (type) => {
            const comp = components.find((c) => c.types?.includes(type));
            return comp?.longText || comp?.shortText || '';
        };

        const streetNumber = get('street_number');
        const route = get('route');
        const subpremise = get('subpremise');

        return {
            full: place.formattedAddress || '',
            flat: subpremise || streetNumber || '',
            street: route || '',
            suburb: get('locality') || get('sublocality') || get('sublocality_level_1') || '',
            postalCode: get('postal_code') || '',
            state: get('administrative_area_level_1') || '',
            country: get('country') || ''
        };
    };

    return {
        suggestions,
        loading,
        search,
        getPlaceDetails
    };
}
