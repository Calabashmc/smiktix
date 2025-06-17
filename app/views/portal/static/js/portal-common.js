import {tomSelectInstances} from '../../../../static/js/includes/tom-select.js';
import {getCurrentUser} from '../../../../static/js/includes/utils.js';

export async function handleMeButton() {
    const requestedBy = document.getElementById('requested-by')
    const requestedByTomSelect = await tomSelectInstances.get(requestedBy.id);
    const currentUser = await getCurrentUser();

    requestedBy.value = currentUser['user_id'];
    // Set value using the TomSelect instance
    if (requestedByTomSelect) {
        requestedByTomSelect.setValue([currentUser['user_id']]);
    }
}