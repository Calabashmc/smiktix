import {showSwal} from '../../../../static/js/includes/form-classes/form-utils.js';
import {deleteColumn} from '../../../../static/js/table.js';
import {priorityButtonsClass} from '../../../problem/static/js/includes/problem-priority-button-class.js';
import {CustomTabulator} from '../../../../static/js/table.js';
import {ChartManager} from '../../../../static/js/includes/dashboard-graphs.js';
import {filterFieldListener, populate_admin_form} from './config-admin/admin-common-functions.js';
import {problemDashboard} from '../../../problem/static/js/problem-dashboard.js';
import {handleRowDelete} from './config-admin/table-edit.js';
import {fetchSupportAgents} from '../../../../static/js/includes/support-agents.js';

const timezone = Intl.DateTimeFormat().resolvedOptions().timeZone;

class ProblemAdminDashboard {
    constructor() {
        this.clearFilterBtn = document.getElementById('clear-filter-btn')
        this.createdBy = document.getElementById('created-by');
        this.downloadBtn = document.getElementById('download-csv')
        this.filterField = document.getElementById('problem-filter-field');
        this.filterValue = document.getElementById('problem-filter-value');
        this.form = document.getElementById('form');
        this.priority = document.getElementById('priority');
        this.problemForm = document.getElementById('problem-admin-offcanvas');
        this.problemOffCanvas = new bootstrap.Offcanvas(this.problemForm);
        this.requestedBy = document.getElementById('requested-by');
        this.saveBtn = document.getElementById('submit-btn');
        this.shortDesc = document.getElementById('short-desc');
        this.status = document.getElementById('status-select');
        this.supportedBy = document.getElementById('support-agent');
        this.supportTeam = document.getElementById('support-team');
        this.ticketNumber = document.getElementById('ticket-number');
        this.ticketType = document.getElementById('ticket-type');
    }

    async init() {
        await this.initialiseAdminProblemsTable();
        this.problemTabMap = this.initialiseProblemTabMap();
        this.chartManager = new ChartManager(this.problemTabMap);
        // initaliseTomSelectFields();
        this.setupListeners();
    }

    setupListeners() {
        filterFieldListener(this.adminProblemsTable, this.filterField, this.filterValue);

        this.clearFilterBtn.addEventListener('click', () => {
            this.chartManager.triggerDoubleClick('all-problems-priority-count', 'All');
        });

        this.downloadBtn.addEventListener('click', () => {
            this.adminProblemsTable.downloadDialog('csv', this.adminProblemsTable);
        });

        this.form.addEventListener('input', () => {
            this.saveBtn.disabled = false; // Enable the button
        });

        this.saveBtn.addEventListener('click', async () => {
            await this.updateRecord();
        });

        this.supportTeam.addEventListener('change', async () => {
            await fetchSupportAgents(this.supportTeam.options[this.supportTeam.selectedIndex].value);
        });

    }

    // Function to initialize the adminTicketsTable
    async initialiseAdminProblemsTable() {
        this.adminProblemsTable = new CustomTabulator(
            '/api/get_paginated/',
            '#all-problems-table',
            {
                'scope': 'all',
                'timezone': timezone,
                'model': 'problem'
            },
            await this.getProblemColumns(),
            true,
        );

        this.adminProblemsTable.setRowDblClickEventHandler(async (e, row) => {
            await populate_admin_form('problem', '/api/get-problem-ticket/', row);
            this.problemOffCanvas.show();
            this.saveBtn.disabled = true;
            priorityButtonsClass.setPriorityButton();
        });

        const tableInstance = this.adminProblemsTable.getTableInstance()
        tableInstance.on('rowDeleted', (row) => handleRowDelete('problem', row));
    }

    async updateRecord() {
        const response = await fetch('/api/update_table_row/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                'created_by_id': this.createdBy.options[this.createdBy.selectedIndex].value,
                'model': 'Problem',
                'priority': this.priority.value,
                'requested_by': this.requestedBy.value,
                'short_desc': this.shortDesc.value,
                'status': this.status.value,
                'supporter_id': this.supportedBy.value,
                'support_team_id': this.supportTeam.value,
                'ticket_number': this.ticketNumber.value,
                'ticket-type': this.ticketType.value,
            })
        })

        if (response.ok) {
            await showSwal('Success', 'Ticket Updated', 'success');
            this.problemOffCanvas.hide();
            await this.initialiseAdminProblemsTable();
        }
    }

    // Function to initialize the interactionTabMap
    initialiseProblemTabMap() {
        return {
            'problems-pane': {
                combined: {
                    api: '/api/get-open-by-type-count/',
                    div: 'all-problems-type-count',
                    chart: 'bar',
                    title: 'All Open Problems',
                    xLabel: 'types',
                    scope: 'all',
                    model: 'Problem',
                    ticket_type: 'problem',
                    table: this.adminProblemsTable
                },
                priority: {
                    api: '/api/get-open-tickets-priority-count/',
                    div: 'all-problems-priority-count',
                    chart: 'bar',
                    title: 'Open by Priority',
                    xLabel: 'priorities',
                    scope: 'all',
                    model: 'Problem',
                    ticket_type: 'problem',
                    table: this.adminProblemsTable
                },
                status: {
                    api: '/api/get-open-tickets-status-count/',
                    div: 'all-problems-status-count',
                    chart: 'pie',
                    title: 'Open By Status',
                    xLabel: 'status',
                    scope: 'all',
                    model: 'Problem',
                    ticket_type: 'problem',
                    table: this.adminProblemsTable
                },
            }
        };
    }

    async getProblemColumns() {
        this.problemColumns = await problemDashboard.getProblemColumns();
        this.problemColumns.push(deleteColumn)
        return this.problemColumns
    }
}

const problemAdminDashboard = new ProblemAdminDashboard();
await problemAdminDashboard.init();