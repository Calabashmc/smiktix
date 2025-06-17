import {showSwal} from './form-classes/form-utils.js';

const ticketForm = document.getElementById('form');

export function formValidationListener() {
    ticketForm.addEventListener('submit', async (e) => {
        // add was-validated to display custom colors
        ticketForm.classList.add('was-validated');
        e.preventDefault();
        if (validateForm()) {
            ticketForm.submit();
        } else {
            await showSwal('', 'Fill in all required fields', 'warning');
        }
    });
}

export function validateForm() {
    let isValid = true;
    for (let i = 0; i < ticketForm.elements.length; i++) {
        const element = ticketForm.elements[i];

        // Skip validation for disabled fields
        if (element.disabled) {
            console.log(`Skipping validation for disabled field: ${element.name}`);
            continue;
        }

        if (element.hasAttribute('required')) {
            if (!element.checkValidity() || element.value.trim() === '') {
                console.log(`Invalid field: ${element.name} is required ${element.hasAttribute('required')}`);
                isValid = false;
                element.classList.add('is-invalid');
            }
        }

        // Custom validation for category_id (ensure not 0)
        if (element.name === 'category_id' && element.value === '0') {
            isValid = false;
            element.classList.add('is-invalid');
        }
    }
    return isValid;
}

