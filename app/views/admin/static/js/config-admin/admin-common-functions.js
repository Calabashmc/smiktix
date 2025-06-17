import {TabulatorFull as Tabulator} from '../../../../../static/js/tabulator/tabulator_esm.js';
import {CustomTabulator, deleteColumn} from '../../../../../static/js/table.js';
import {blankFieldWarning, handleRowAdd, handleRowDelete, handleTableEdit} from './table-edit.js';
import {initaliseTomSelectFields, tomSelectInstances} from '../../../../../static/js/includes/tom-select.js';
import {fetchSupportAgents} from '../../../../../static/js/includes/support-agents.js';

async function createTable(model, divId, columns, filterField) {
    // CustomTabulator -> constructor(url, selector, args, columns) function in table.js
    const table = new CustomTabulator(
        '/api/get-lookup-records/',
        divId,
        {model: model, filter_by: filterField},
        await columns,
        false, // Don't paginate
        'filter-info',
        'model',
    );

    const tableInstance = table.getTableInstance();
    // tableInstance.on('rowDblClick', (e) => handleRowDblClick(model, e));
    tableInstance.on('cellEdited', (cell) => handleTableEdit(model, cell));
    tableInstance.on('rowDeleted', (row) => handleRowDelete(model, row));

    return table;
}

export async function initialiseGenericTable({model, filterField = null, divId, columns, addBtn, fields, buildRecord}) {
    const table = await createTable(model, divId, columns, filterField);
    // not all tables have an option to add a row so test
    if (addBtn) {
        addBtn.addEventListener('click', async () => {
            let valid = true;

            // Check if all fields have values
            for (const field of Object.entries(fields)) {
                if (!field[1].value) {
                    valid = false;
                    break;
                }
            }

            if (!valid) {
                await blankFieldWarning();
            } else {
                const record = buildRecord(fields);  // Build the record using dynamic fields
                const success = await handleRowAdd(model, record);

                if (success) {
                    const tableInstance = table.getTableInstance()
                    tableInstance.addRow(record, true);
                    // Clear all fields
                    for (const field of Object.values(fields)) {
                        field.value = '';
                    }
                }
            }
        });
    }
    return table
}


export function filterFieldListener(table, filterByField, filter) {
    let timeout;
    // Handler to apply the filter based on the selected field and input value
    const applyFilter = () => {
        clearTimeout(timeout);
        timeout = setTimeout(() => {
            const filterBy = filterByField.value;
            if (filterBy) {
                filterTable(table, filterBy, filter.value);  // Apply the filter with the selected field
            } else {
                table.table.clearFilter();  // Clear the filter if no option is selected
            }
        }, 300);  // Set the debounce delay
    };

    // Event listener for the change in the filter field
    filterByField.addEventListener('change', () => {
        filter.value = '';
        filter.disabled = !filterByField.value;  // Enable/disable the filter input based on selection
        applyFilter();  // Apply filter or clear immediately when the field changes
    });

    // Event listener for keyup in the filter input with debouncing
    filter.addEventListener('keyup', applyFilter);
}

function filterTable(table, filterBy, filterValue) {
    table.table.setFilter(filterBy, 'like', filterValue);  // Apply the filter
}

export function setTomSelectByText(selectId, text) {
    const tomSelect = tomSelectInstances.get(selectId);

    if (!tomSelect) {
        console.warn(`TomSelect instance with ID '${selectId}' not found.`);
        return false;
    }

    for (const [value, item] of Object.entries(tomSelect.options)) {
        if (item.text === text) {
            tomSelect.setValue(value, true);
            return value; // Return the ID (value) of the selected option
        }
    }

    console.warn(`Option with text '${text}' not found in TomSelect with ID '${selectId}'`);
    return false;
}


// Set TomSelect option by ID
export function setTomSelectById(selectId, id) {
    const tomSelect = tomSelectInstances.get(selectId);

    if (!tomSelect) {
        console.warn(`TomSelect instance with ID '${selectId}' not found.`);
        return false;
    }

    if (Array.isArray(id)) { // Handle an array of IDs for multi-select inputs
        const validIds = id.filter((item) => tomSelect.options[item]);
        if (validIds.length > 0) {
            tomSelect.setValue(validIds, true); // Set all valid IDs
            return true;
        }
    } else if (tomSelect.options[id]) {
        tomSelect.setValue(id, true); // Set the single ID
        return true;
    }

    console.warn(`No matching options found for ID(s): ${id}`);
    return false;
}


async function interactionColumns() {
    return [
        {
            title: '#',
            headerHozAlign: 'center',
            field: 'ticket_number',
            hozAlign: 'center',
        },
        {
            title: 'Type',
            headerHozAlign: 'center',
            field: 'ticket_type',
            hozAlign: 'center',
        },
        {
            title: 'Priority',
            headerHozAlign: 'center',
            field: 'priority',
            hozAlign: 'center',
        },
        {
            title: 'Status',
            headerHozAlign: 'center',
            field: 'status',
            hozAlign: 'center',
        },
        {
            title: 'Requester',
            field: 'requested_by',
        },
        {
            title: 'Supporter',
            field: 'supported_by',
        },
        {
            title: 'Team',
            field: 'support_team',
        },
        {
            title: 'Short Description',
            field: 'short_desc'
        },
        deleteColumn
    ]
}

async function problemColumns() {
    return [
        {
            title: 'Ticket #',
            field: 'ticket_number',
            hozAlign: 'center',
            headerHozAlign: 'center',
        },
        {
            title: 'Type',
            field: 'ticket_type',
            headerHozAlign: 'center',
        },
        {
            title: 'Priority',
            field: 'priority',
            hozAlign: 'center',
        },
        {
            title: 'Status',
            field: 'status',
        },
        {
            title: 'Requester',
            field: 'requested_by',
        },
        {
            title: 'Supported By',
            field: 'supported_by',
        },
        {
            title: 'Short Description',
            field: 'shortDesc'
        },
        {
            title: 'Created',
            field: 'created'
        },
        deleteColumn
    ]
}

async function populateChildTicketTable(model, data) {
    // get columns for model
    let columns;

    switch (model) {
        case 'problem':
            columns = await interactionColumns(); // Child tickets for Problem are Incidents
            model = 'interaction'; // used for url when row dbl-clicked
            break;
        case 'change':
            columns = await problemColumns(); // Child tickets for Change are Problems
            model = 'problem'; // used for url when row dbl-clicked
            break;
        case 'incident':
            columns = await interactionColumns(); // Child tickets for Incident are Incidents
            model = 'interaction'; // used for url when row dbl-clicked
            break;
    }

    const childTable = new Tabulator('#child-tickets-table', {
        data: data, //assign data to table
        layout: 'fitColumns',
        pagination: 'local',
        paginationSize: 10,
        paginationSizeSelector: [10, 20, 30, 40],
        paginationCounter: 'rows',
        placeholder: 'No Data Set',
        columns: columns,
    });

    childTable.on('rowDblClick', (e, row) => {
        const ticketNumber = row.getData().ticket_number;
        window.open(`/ui/${model.toLowerCase()}/ticket/?ticket=${ticketNumber}`, '_blank');
    })

    childTable.on('rowDeleted', (row) => handleRowDelete('Problem', row));
}

export async function populate_admin_form(model, url, row) {
    const ticketType = document.getElementById('ticket-type');
    const ticketNumber = document.getElementById('ticket-number');

    await initaliseTomSelectFields();

    const response = await fetch(`${url}?ticket-number=${row.getData().ticket_number}`);
    const data = await response.json();


    ticketType.innerText = data['ticket-type'] || '';
    ticketNumber.innerText = data['ticket-number'] || '';
    // Populate support agents select based on team so agent can be set
    if (data['support-team']) {
        const team_id = setTomSelectByText('support-team', data['support-team']);
        await fetchSupportAgents(team_id);
    }

    // If ticket has child tickets (Problem, Change) show them
    if (data['child_tickets']) {
        await populateChildTicketTable(model, data['child_tickets']);
    }

    for (const [key, value] of Object.entries(data)) {
        const field = document.getElementById(key);
        if (field) {
            if (value === null || value === undefined) {
                // Clear the field if the value is null or undefined
                if (tomSelectInstances.has(key)) {
                    // Clear Tom Select field
                    const tomSelectInstance = tomSelectInstances.get(key);
                    tomSelectInstance.clear(); // Clear the Tom Select
                } else if (field.type === 'checkbox') {
                    field.checked = false; // Clear checkbox
                } else {
                    field.value = ''; // Clear input field
                }
            } else {
                if (tomSelectInstances.has(key)) {
                    const result = setTomSelectByText(key, value);
                    if (!result) {
                        setTomSelectById(key, value);
                    }
                } else if (field.type === 'checkbox') {
                    field.checked = value;
                } else {
                    field.value = value;
                }
            }
        }
    }
}