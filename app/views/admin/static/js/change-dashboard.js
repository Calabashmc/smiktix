import {showSwal} from '../../../../static/js/includes/form-classes/form-utils.js';
import {deleteColumn} from '../../../../static/js/table.js';

import {CustomTabulator} from '../../../../static/js/table.js';
import {ChartManager} from '../../../../static/js/includes/dashboard-graphs.js';
import {filterFieldListener, populate_admin_form} from './config-admin/admin-common-functions.js';
import {changeDashboard} from '../../../change/static/js/change-dashboard.js';
import {initaliseTomSelectFields} from '../../../../static/js/includes/tom-select.js';
import {fetchSupportAgents} from '../../../../static/js/includes/support-agents.js';

const timezone = Intl.DateTimeFormat().resolvedOptions().timeZone;

export class ChangeAdminDashboard {
    constructor() {
        this.changeForm = document.getElementById('change-admin-offcanvas');
        this.changeOffCanvas = new bootstrap.Offcanvas(this.changeForm);
        this.clearFilterBtn = document.getElementById('clear-filter-btn');
        this.createdBy = document.getElementById('created-by');
        this.downloadCsvBtn = document.getElementById('download-csv');
        this.filterField = document.getElementById('change-filter-field');
        this.filterValue = document.getElementById('change-filter-value');
        this.form = document.getElementById('form');
        this.priority = document.getElementById('priority');
        this.requestedBy = document.getElementById('requested-by');
        this.saveBtn = document.getElementById('submit-btn');
        this.shortDesc = document.getElementById('short-desc');
        this.status = document.getElementById('status-select');
        this.supportedBy = document.getElementById('support-agent');
        this.supportTeam = document.getElementById('support-team');
        this.ticketNumber = document.getElementById('ticket-number');
        this.tickettype = document.getElementById('ticket-type');
    }

    async init() {
        await this.initialiseAdminChangesTable();
        this.initialiseProblemTabMap();
        this.chartManager = new ChartManager(this.changeTabMap);
        // initaliseTomSelectFields();
        this.setupListeners();
    }

    setupListeners() {
        filterFieldListener(this.adminChangesTable, this.filterField, this.filterValue);

        this.clearFilterBtn.addEventListener('click', () => {
            this.chartManager.triggerDoubleClick('all-changes-priority-count', 'All');
        });

        this.downloadCsvBtn.addEventListener('click', () => {
            this.adminChangesTable.downloadDialog('csv', this.adminChangesTable);
        });

        this.supportTeam.addEventListener('change', async () => {
            await fetchSupportAgents(this.supportTeam.options[this.supportTeam.selectedIndex].value);
        });

        this.form.addEventListener('input', () => {
            this.saveBtn.disabled = false; // Enable the button
        });

        this.saveBtn.addEventListener('click', async () => {
            await this.updateRecord();
        });
    }

    // Function to initialize the adminTicketsTable
    async initialiseAdminChangesTable() {
        this.adminChangesTable = new CustomTabulator(
            '/api/get_paginated/',
            '#all-changes-table',
            {
                'scope': 'all',
                'timezone': timezone,
                'model': 'Change'
            },
            await this.getChangeColumns(),
            true,
            'filter-info'
        );

        this.tableInstance = this.adminChangesTable.getTableInstance()
        this.tableInstance.on('rowDblClick', async (e, row) => {
            await populate_admin_form('Change', '/api/change/get-change-ticket/', row);
            this.changeOffCanvas.show();
            this.saveBtn.disabled = true;
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
                'model': 'Change',
                'priority': this.priority.value,
                'requested_by': this.requestedBy.value,
                'short_desc': this.shortDesc.value,
                'status': this.status.value,
                'supporter_id': this.supportedBy.value,
                'support_team_id': this.supportTeam.value,
                'ticket_number': this.ticketNumber.value,
                'ticket-type': this.tickettype.value,
            })
        })

        if (response.ok) {
            await showSwal('Success', 'Ticket Updated', 'success');

            this.changeOffCanvas.hide();
            this.tableInstance.destroy();
            await this.initialiseAdminChangesTable();
        }
    }

    // Function to initialize the interactionTabMap
    initialiseProblemTabMap() {
        this.changeTabMap = {
            'changes-tab-pane': {
                type: {
                    api: '/api/get-open-by-type-count/',
                    div: 'all-change-types-count',
                    chart: 'bar',
                    title: 'All Change by Type',
                    xLabel: 'change_type',
                    scope: 'all',
                    model: 'Change',
                    ticket_type: 'change',
                    table: this.adminChangesTable
                },
                risk: {
                    api: '/api/get-open-tickets-priority-count/',
                    div: 'all-normal-risk-count',
                    chart: 'bar',
                    title: 'All Normal Change by Risk',
                    xLabel: 'risk',
                    scope: 'all',
                    model: 'Change',
                    ticket_type: 'change',
                    table: this.adminChangesTable
                },
                status: {
                    api: '/api/get-open-tickets-status-count/',
                    div: 'all-changes-status-count',
                    chart: 'pie',
                    title: 'All Open By Status',
                    xLabel: 'status',
                    scope: 'all',
                    model: 'Change',
                    ticket_type: 'change',
                    table: this.adminChangesTable
                },
            },
        }
    }

    async getChangeColumns() {
        this.changeColumns = await changeDashboard.getChangeColumns();
        this.changeColumns.push(deleteColumn)
        return this.changeColumns
    }

}

const changeAdminDashboard = new ChangeAdminDashboard();
await changeAdminDashboard.init();