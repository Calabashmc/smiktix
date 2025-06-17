import {CustomTabulator, unlinkColumn} from '../table.js';
import {tomSelectInstances} from './tom-select.js';
import {showSwal} from './form-classes/form-utils.js';

const timezone = Intl.DateTimeFormat().resolvedOptions().timeZone;

// populate child ticket tables
export class ChildrenClass {
    constructor(tableColumns) {
        this.childModal = document.getElementById('children-modal');

        if (this.childModal) {
            this.childIdModal = new bootstrap.Modal(this.childModal);
        }

        this.childModalHelpBtn = document.getElementById('child-modal-help-btn');
        this.childIdSetBtn = document.getElementById('modal-set-child-id-btn');
        this.childIdCancelBtn = document.getElementById('modal-cancel-child-id-btn');
        this.childCount = document.getElementById('child-count');
        this.childSelect = document.getElementById('child-select');
        this.tabChildCount = document.getElementById('child-count');
        this.tableColumns = tableColumns;
        this.openChildSelectModalBtn = document.getElementById('child-btn');
        this.parentTicketNumber = document.getElementById('parent-ticket-number') ||
            document.getElementById('ticket-number');
        this.status = document.getElementById('status');
        this.ticketNumber = document.getElementById('ticket-number');
        this.ticketType = document.getElementById('ticket-type');
    }

    async init() {
        this.setUpListeners();
        await this.populateChildTicketTable();
    }

    setUpListeners() {
        this.childModalHelpBtn.addEventListener('click', async () => {
            await showSwal(
                'Info',
                '<p>If a ticket is set as a Parent, or is a child of another ticket, they will not be available for selection</p>' +
                '<p>The child ticket\'s status will be changed to match the Problem status</p>',
                'info'
            );
        })

        this.openChildSelectModalBtn.addEventListener('click', () => {
            this.clearChildSelect();
            this.childIdModal.show();
        });

        // add button on child add modal
        this.childIdSetBtn.addEventListener('click', async () => {
            if (this.childSelect.value === '') {
                await showSwal('Error', 'Please select a child ticket', 'error');
                return;
            }
            await this.setChildId();
            this.childIdModal.hide();
        });

        // cancel button on child add modal
        this.childIdCancelBtn.addEventListener('click', () => {
            this.childIdModal.hide();
        });
    }

    clearChildSelect() {
        const childSelectId = this.childSelect.id; // Get the ID of childSelect
        const tomSelect = tomSelectInstances.get(childSelectId);

        if (tomSelect) {
            tomSelect.clear();
        } else {
            console.warn(`TomSelect instance for childSelect with ID '${childSelectId}' not found.`);
        }
    }

    // Adds a child ticket to the parent via API call. Child status is also updated to match the Problem status
    async setChildId() {
        const childSelection = this.childSelect.options[this.childSelect.selectedIndex].text;
        const [childTicketNumber, childType] = childSelection.split(' | ');

        const apiArgs = {
            'parent-type': this.ticketType.value,
            'parent-ticket-number': this.parentTicketNumber.value,
            'child-type': childType.trim(),
            'child-ticket-number': childTicketNumber.trim(),
        };

        const response = await fetch(`/api/add-children/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(apiArgs)
        });

        const data = await response.json();

        if (!response.ok) {
            await showSwal('Error', data['error'], 'error');
        } else {
            await this.populateChildTicketTable();
        }
    }

    async populateChildTicketTable() {
        const childTicketsTable = await new CustomTabulator(
            '/api/get-children/',
            '#child-tickets-table',
            {
                'parent_ticket_number': this.ticketNumber.value,
                'parent_type': this.ticketType.value,
                'timezone': timezone,
            },
            this.getColumns(),
            true,
        );

        const tableInstance = childTicketsTable.getTableInstance();
        const numberOfRows = await childTicketsTable.numberOfRows();
        this.childCount.innerHTML = `[${numberOfRows}]`;

        childTicketsTable.setRowDblClickEventHandler(async (e, row) => {
            let urlType;
            const ticketNumber = row.getData().ticket_number;
            const ticketType = row.getData().ticket_type;

            if (['Incident', 'Request'].includes(ticketType)) {
                urlType = 'interaction';
            } else if (['Problem', 'Known Error'].includes(ticketType)) {
                urlType = 'problem';
            } else {
                urlType = 'release';
            }

            window.open(`/ui/${urlType}/ticket/?ticket=${ticketNumber}`, '_blank');
        });

        tableInstance.on('rowDeleted', (row) => this.removeChild(tableInstance, row));
    }

    getColumns() {
        this.tableColumns.pop(unlinkColumn); // remove unlink column else multiple unlink buttons will be added
        this.tableColumns.push(unlinkColumn);
        return this.tableColumns;
    }

    async removeChild(tableInstance, row) {
        const apiArgs = {
            'parent-type': this.ticketType.value,
            'parent-ticket-number': this.parentTicketNumber.value,
            // get child details from the tabular table
            'ticket-type': row.getData().ticket_type,
            'ticket-number': row.getData().ticket_number,
        };

        const response = await fetch(`/api/unlink-children/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(apiArgs)
        });

        const data = await response.json();

        if (!response.ok) {
            await showSwal('Error', `Child ticket could not be detached ${data['error']}`, 'error');
        } else {
            await showSwal('Success', `${data['message']}`, 'success');
            this.tabChildCount.innerHTML = `[${tableInstance.getDataCount()}]`;
        }
    }

}
