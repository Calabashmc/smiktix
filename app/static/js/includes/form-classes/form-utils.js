const formVars = document.getElementById('form-vars');
const existsString = formVars.dataset.exists;
export const exists = existsString === 'true'


export function showFormButtons() {
    document.getElementById('submit-btn').hidden = false;
    document.getElementById('cancel-btn').hidden = false;
}

export function hideFormButtons() {
    document.getElementById('submit-btn').hidden = true;
    document.getElementById('cancel-btn').hidden = true;
}


export async function showSwal(
    title,
    message,
    alertType = 'question',
    toast = true,
    position = 'center',
    showConfirmButton = true
) {
    // shows a swal alert with a title and message and an icon. Default icon is 'question' which will
    // show an Ok and a Cancel button. Other types just show an OK button.
    let icon = alertType;
    let showCancel = false;
    let timer = undefined;

    if (['question'].includes(alertType)) {
        showCancel = true;
        showConfirmButton = true
        timer = undefined
    }

    if (['warning'].includes(alertType)) {
        showConfirmButton = true;
        timer = undefined;
    }

    if (['success'].includes(alertType)) {
        showConfirmButton = false;
        timer = 2000;
    }

    if (['error', 'info'].includes(alertType)) {
        timer = 8000;
    }
    return await Swal.fire({
        toast: toast,
        position: position,
        title: title || message, // Use message as title if empty
        html: title ? message : '', // Set text only if title is provided
        icon: icon,
        showCancelButton: showCancel,
        confirmButtonText: 'Ok',
        cancelButtonText: 'Cancel',
        customClass: {
            confirmButton: 'btn btn-primary ms-auto me-2', // use bootstrap button classes
            cancelButton: 'btn btn-danger'
        },
        buttonsStyling: false, // Disable default SweetAlert2 styles
        showConfirmButton: showConfirmButton, // hide confirm button for warnings,
        timer: timer,
    });
}

export async function saveNotes(worklog, is_system = false) {
    const ticketNumber = document.getElementById('ticket-number');
    const ticketType = document.getElementById('ticket-type');

    if (typeof is_system === 'undefined') {
        is_system = false; // If is_system is not provided or is undefined, set it to false
    }

    // because worklog can be a string or array. e.g. form-button-handlers.js handleSubmitBtn sends array.
    // so convert to a string if an Array else leave it be.
    const formattedString = `${Array.isArray(worklog) ? worklog.join('\n') : worklog}`;

    let apiArgs = {
        'ticket_number': ticketNumber.value,
        'ticket_type': ticketType.value,
        'note': formattedString, //formattedString,
        'is_system': is_system,
    };

    const response = await fetch(`/api/save-worknote/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(apiArgs)
    })
    const data = await response.json();

    if (!response.ok) {
        await showSwal('Error', `Unable to save worklog ${data.error}`, 'error');
    } else {
        // trigger event to notify journal-class.js.
        // import {journalClass} from '../journal-class.js' is problematic
        const event = new Event('worklog-saved');
        document.dispatchEvent(event);
    }
}

export function setTodaysDate(fieldId) {
    const field = document.getElementById(fieldId);
    if (!field) return;

    const now = new Date();
    let value;

    switch (field.type) {
        case 'date':
            value = now.toISOString().split('T')[0];
            break;
        case 'datetime':
        case 'datetime-local':
            value = now.toISOString().slice(0, 16);
            break;
        default:
            return;
    }

    field.value = value;
}

export function enableToolTips() {
    // Initialize Bootstrap tooltips
    const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle=\'tooltip\']')
    const tooltipList = [...tooltipTriggerList].map(tooltipTriggerEl => new bootstrap.Tooltip(tooltipTriggerEl))

    // Handle tooltips for Tom Select elements
    document.querySelectorAll('.ts-wrapper').forEach(wrapper => {
        const select = wrapper.previousElementSibling; // The hidden original select
        if (select && select.dataset.bsTitle) {
            wrapper.setAttribute('data-bs-toggle', 'tooltip');
            wrapper.setAttribute('data-bs-title', select.dataset.bsTitle);
            new bootstrap.Tooltip(wrapper);
        }
    });
}