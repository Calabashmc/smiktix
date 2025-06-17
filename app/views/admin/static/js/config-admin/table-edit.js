import {showSwal} from '../../../../../static/js/includes/form-classes/form-utils.js';

export async function handleTableEdit(model, cell) {
    const url = '/api/lookup/set-table-row/'
    const changedRowData = cell.getRow().getData(); // Get the entire row data

    // Add the model property to the row data
    const dataToSend = {model: model, ...changedRowData};
    // Send the changed row or cell data to the API
    await fetch(url, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(dataToSend),
    });
}


export async function handleRowDelete(model, row) {
    const url = '/api/delete_table_row/'
    const changedRowData = row.getData(); // Get the entire row data
    const dataToSend = {model: model, ...changedRowData};
    console.log(dataToSend)
    // Send the changed row or cell data to the API
    await fetch(url, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(dataToSend),
    });
}

export async function handleRowAdd(model, record) {
    // Check if the record is a string, and if so, parse it into an object
    if (typeof record === 'string') {
        try {
            record = JSON.parse(record);
        } catch (e) {
            console.error('Error parsing record:', e);
            return;
        }
    }
    const dataToSend = {model: model, ...record};

    const response = await showSwal('Add New Record?', 'Users will need to refresh the page to see the new record.', 'question');

    if (response.isConfirmed) {
        const response = await fetch('/api/lookup/set-table-row/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(dataToSend),
        });
        if (!response.ok) {
            const errorData = await response.json();
            console.error('Error:', errorData);
            await showSwal('Error', errorData.error || 'Record could not be added', 'error');
            return false;
        }
        return true;
    } else {
        return false;
    }
}


export async function blankFieldWarning() {
    await showSwal('Blank Field', 'Record field(s) cannot be blank.', 'warning');
    return false

}
