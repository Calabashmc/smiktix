import {showSwal} from '../../../../static/js/includes/form-classes/form-utils.js';
import {deleteColumn} from '../../../../static/js/table.js';
import {fetchSupportAgents} from '../../../../static/js/includes/support-agents.js';
import {CustomTabulator} from '../../../../static/js/table.js';
import {ChartManager} from '../../../../static/js/includes/dashboard-graphs.js';
import {filterFieldListener, populate_admin_form} from './config-admin/admin-common-functions.js';
import {interactionDashboard} from '../../../interaction/static/js/interaction-dashboard.js';
import {handleRowDelete, handleTableEdit} from './config-admin/table-edit.js';
import {initaliseTomSelectFields} from '../../../../static/js/includes/tom-select.js';
import {priorityButtonsClass} from '../../../interaction/static/js/includes/interaction-priority-button-class.js';

const timezone = Intl.DateTimeFormat().resolvedOptions().timeZone;

class InteractionAdminDashboard {
    constructor() {
        this.category = document.getElementById('category-id');
        this.clearFilterBtn = document.getElementById('clear-filter-btn');
        this.createdBy = document.getElementById('created-by');
        this.downloadBtn = document.getElementById('download-csv');
        this.filterField = document.getElementById('filter-field');
        this.filterValue = document.getElementById('filter-value');
        this.form = document.getElementById('form');
        this.impact = document.getElementById('priority-impact');
        this.interactionForm = document.getElementById('interaction-admin-offcanvas');
        this.interactionOffCanvas = new bootstrap.Offcanvas(this.interactionForm);
        this.isMajor = document.getElementById('is-major');
        this.priority = document.getElementById('priority');
        this.respondBy = document.getElementById('respond-by');
        this.resolveBy = document.getElementById('resolve-by');
        this.saveBtn = document.getElementById('submit-btn');
        this.status = document.getElementById('status-select');
        this.supportedBy = document.getElementById('support-agent');
        this.supportTeam = document.getElementById('support-team');
        this.shortDesc = document.getElementById('short-desc');
        this.ticketNumber = document.getElementById('ticket-number');
        this.ticketType = document.getElementById('ticket-type');
        this.urgency = document.getElementById('priority-urgency');
    }

    async init() {
        await this.initialiseAdminTicketsTable();
        this.interactionTabMap = await this.initialiseInteractionTabMap()
        this.chartManager = new ChartManager(this.interactionTabMap);
        // initaliseTomSelectFields()
        this.setupListeners();
    }


    setupListeners() {
        filterFieldListener(this.allTicketsTable, this.filterField, this.filterValue);

        this.clearFilterBtn.addEventListener('click', () => {
            this.chartManager.triggerDoubleClick('all-type-count', 'All');
        });

        this.downloadBtn.addEventListener('click', () => {
            this.allTicketsTable.downloadDialog('csv', this.allTicketsTable);
        });

        this.form.addEventListener('input', () => {
            this.saveBtn.disabled = false; // Enable the button
        });

        this.resolveBy.addEventListener('change', async () => {
            await this.checkSlaTimes();
        })

        this.respondBy.addEventListener('change', async () => {
            await this.checkSlaTimes();
        })

        this.saveBtn.addEventListener('click', async () => {
            await this.updateRecord()
        });

        this.supportTeam.addEventListener('change', async () => {
            await fetchSupportAgents(this.supportTeam.options[this.supportTeam.selectedIndex].value);
        });
    }

    // Function to initialize the allTicketsTable
    async initialiseAdminTicketsTable() {
        this.allTicketsTable = new CustomTabulator(
            '/api/get_paginated/',
            '#all-tickets-table',
            {
                'scope': 'all',
                'timezone': timezone,
                'model': 'interaction'
            },
            await this.getInteractionColumns(),
            true,
            'filter-info',
        );

        this.tableInstance = this.allTicketsTable.getTableInstance();
        this.tableInstance.on('cellEdited', (cell) => handleTableEdit('Ticket', cell));
        this.tableInstance.on('rowDeleted', (row) => handleRowDelete('Ticket', row));

        this.allTicketsTable.setRowDblClickEventHandler(async (e, row) => {
            await populate_admin_form('Interaction', '/api/interaction/get-incident-ticket/', row);
            this.interactionOffCanvas.show()
            this.saveBtn.disabled = true;
            this.currentRespondByValue = this.respondBy.value // used to reset value when SLA is not 24/7
            await priorityButtonsClass.setPriorityButton();
        });
    }

    async updateRecord() {
        const response = await fetch('/api/update_table_row/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                'created_by_id': this.createdBy.options[this.createdBy.selectedIndex].value,
                'category_id': this.category.value,
                'impact': this.impact.value,
                'is_major': this.isMajor.checked,
                'model': 'Interaction',
                'priority': this.priority.value,
                'short_desc': this.shortDesc.value,
                'sla_respond_by': this.respondBy.value,
                'sla_resolve_by': this.resolveBy.value,
                'status': this.status.value,
                'supporter_id': this.supportedBy.value,
                'support_team_id': this.supportTeam.value,
                'ticket_number': this.ticketNumber.value,
                'ticket-type': this.ticketType.value,
                'urgency': this.urgency.value

            })
        })

        if (response.ok) {
            await showSwal('Success', 'Ticket Updated', 'success');
            this.interactionOffCanvas.hide();
            this.tableInstance.destroy();
            await this.initialiseAdminTicketsTable();
        }
    }

    async checkRespondByInHours() {
        const response = await fetch('/api/check-response-time/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                'priority': this.priority.value,
                'respond_by': this.respondBy.value
            })
        })
        const data = await response.json();
        return !!data['in_hours'];
    }

    async checkSlaTimes() {
        const inHours = await this.checkRespondByInHours();
        if (!inHours) {
            await showSwal('Warning', 'Not a 24/7 SLA so Response time must be in business hours', 'warning');
            this.respondBy.value = this.currentRespondByValue
            return
        }


        const response = await fetch('/api/get-sla-resolve-time/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                'priority': this.priority.value,
                'respond_by': this.respondBy.value
            })
        })

        const data = await response.json();

        if (data) {
            await showSwal(
                'Resolve Time Adjustment',
                `Setting Resolve time for a ${this.priority.value} ticket to Response time + ${data['wait_time']} hours`,
                'info'
            );
            this.resolveBy.value = data['resolve_by']
        }
    }

    async initialiseInteractionTabMap() {
        return {
            'all-tab-pane': {
                combined: {
                    api: '/api/get-open-by-type-count/',
                    div: 'all-type-count',
                    chart: 'bar',
                    title: 'Open Incidents vs Requests',
                    xLabel: 'ticket_type',
                    scope: 'all',
                    model: 'Interaction',
                    ticket_type: 'interaction',
                    table: this.allTicketsTable
                },
                incident: {
                    api: '/api/get-open-tickets-priority-count/',
                    div: 'all-incidents-priority-count',
                    chart: 'bar',
                    title: 'Open Incidents',
                    xLabel: 'priorities',
                    scope: 'all',
                    model: 'Interaction',
                    ticket_type: 'Incident',
                    table: this.allTicketsTable
                },
                request: {
                    api: '/api/get-open-tickets-priority-count/',
                    div: 'all-requests-priority-count',
                    chart: 'bar',
                    title: 'Open Requests',
                    xLabel: 'priorities',
                    scope: 'all',
                    model: 'Interaction',
                    ticket_type: 'Request',
                    table: this.allTicketsTable
                },
                status: {
                    api: '/api/get-open-tickets-status-count/',
                    div: 'all-status-count',
                    chart: 'pie',
                    title: 'Open By Status',
                    xLabel: 'status',
                    scope: 'all',
                    model: 'Interaction',
                    ticket_type: 'interaction',
                    table: this.allTicketsTable
                },
            }
        }
    }

    async getInteractionColumns() {
        // gets existing config from interactionDashboard and adds delete column
        this.interactionColumns = await interactionDashboard.getInteractionColumns();
        this.interactionColumns.push(deleteColumn)
        return this.interactionColumns
    }

}

const interactionAdminDashboard = new InteractionAdminDashboard();
await interactionAdminDashboard.init();