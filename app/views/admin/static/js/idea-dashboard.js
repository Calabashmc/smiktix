import {showSwal} from '../../../../static/js/includes/form-classes/form-utils.js';
import {deleteColumn} from '../../../../static/js/table.js';
import {CustomTabulator} from '../../../../static/js/table.js';
import {ChartManager} from '../../../../static/js/includes/dashboard-graphs.js';
import {filterFieldListener, populate_admin_form} from './config-admin/admin-common-functions.js';
import {ideasDashboard} from '../../../idea/static/js/ideas-dashboard.js';

const timezone = Intl.DateTimeFormat().resolvedOptions().timeZone;

class IdeaAdminDashboard {
    constructor() {
        this.category = document.getElementById('category-id');
        this.clearFilterBtn = document.getElementById('clear-filter-btn');
        this.createdBy = document.getElementById('created-by');
        this.downloadCsvBtn = document.getElementById('download-csv');
        this.filterField = document.getElementById('idea-filter-field');
        this.filterValue = document.getElementById('idea-filter-value');
        this.form = document.getElementById('form');
        this.ideaForm = document.getElementById('idea-admin-offcanvas');
        this.ideaOffCanvas = new bootstrap.Offcanvas(this.ideaForm);
        this.likelihood = document.getElementById('likelihood');
        this.saveBtn = document.getElementById('submit-btn');
        this.shortDesc = document.getElementById('short-desc');
        this.status = document.getElementById('status-select');
        this.ticketType = document.getElementById('ticket-type');
        this.ticketNumber = document.getElementById('ticket-number');
    }

    async init() {
        await this.initialiseAdminIdeasTable();
        await this.initialiseTabMap();
        this.chartManager = new ChartManager(this.ideaTabMap);
        this.setupListeners();
    }

    setupListeners() {
        filterFieldListener(this.adminIdeaTable, this.filterField, this.filterValue);

        this.clearFilterBtn .addEventListener('click', () => {
            this.chartManager.triggerDoubleClick('all-ideas-likelihood-count', 'All');
        });

        this.downloadCsvBtn.addEventListener('click', () => {
            this.adminIdeaTable.downloadDialog('csv', this.adminIdeaTable);
        });

        this.form.addEventListener('input', () => {
            this.saveBtn.disabled = false; // Enable the button
        });

        this.saveBtn.addEventListener('click', async () => {
            await this.updateRecord()
        });
    }

    // Function to initialize the adminTicketsTable
    async initialiseAdminIdeasTable() {
        this.adminIdeaTable = new CustomTabulator(
            '/api/get_paginated/',
            '#all-idea-table',
            {
                'scope': 'all',
                'timezone': timezone,
                'model': 'idea'
            },
            await this.getIdeaColumns(),
            true
        );

        this.tableInstance = this.adminIdeaTable.getTableInstance();
        this.tableInstance.on('rowDblClick', async (e, row) => {
            await populate_admin_form('Idea', '/api/idea/get-idea/', row);
            this.ideaOffCanvas.show()
            this.saveBtn.disabled = true;
        });
    }


    async updateRecord() {
        const response = await fetch('/api/update_table_row/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                'category_id': this.category.value,
                'created_by_id': this.createdBy.options[this.createdBy.selectedIndex].value,
                'likelihood': this.likelihood.value,
                'model': 'Idea',
                'short_desc': this.shortDesc.value,
                'status': this.status.value,
                'ticket_number': this.ticketNumber.value,
                'ticket-type': this.ticketType.value,
            })
        })

        if (response.ok) {
            await showSwal('Success', 'Ticket Updated', 'success');
            this.ideaOffCanvas.hide();
            this.tableInstance.destroy();
            await this.initialiseAdminIdeasTable();
        }
    }

    // Function to initialize the interactionTabMap
    initialiseTabMap() {
        this.ideaTabMap = {
            'ideas-tab-pane': {
                likelihood: {
                    api: '/api/get-likelihood-count/',
                    div: 'all-ideas-likelihood-count',
                    chart: 'bar',
                    title: 'Likelihood of proceeding',
                    xLabel: 'likelihood',
                    scope: 'all',
                    model: 'Idea',
                    ticket_type: 'Idea',
                    table: this.adminIdeaTable
                },
                category: {
                    api: '/api/get-open-tickets-category-count/',
                    div: 'all-ideas-category-count',
                    chart: 'horizontalBar',
                    title: 'Ideas by Category',
                    xLabel: 'count',
                    scope: 'all',
                    model: 'Idea',
                    ticket_type: 'Idea',
                    table: this.adminIdeaTable
                },
                status: {
                    api: '/api/get-open-tickets-status-count/',
                    div: 'all-ideas-status-count',
                    chart: 'pie',
                    title: 'All Open By Status',
                    xLabel: 'status',
                    scope: 'all',
                    model: 'Idea',
                    ticket_type: 'Idea',
                    table: this.adminIdeaTable
                },
            },
        }
    }

    async getIdeaColumns() {
        this.ideaColumns = await ideasDashboard.getIdeasColumns();
        this.ideaColumns.push(deleteColumn)
        return this.ideaColumns
    }

}

const ideaAdminDashboard = new IdeaAdminDashboard();
await ideaAdminDashboard.init();