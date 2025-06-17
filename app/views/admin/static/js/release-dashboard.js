import {filterFieldListener, populate_admin_form} from './config-admin/admin-common-functions.js';
import {fetchSupportAgents} from '../../../../static/js/includes/support-agents.js';
import {ChartManager} from '../../../../static/js/includes/dashboard-graphs.js';
import {CustomTabulator} from '../../../../static/js/table.js';
import {handleRowDelete} from './config-admin/table-edit.js';

class ReleaseAdminDashboard {
    constructor() {
        this.clearFilterBtn = document.getElementById('clear-filter-btn')
        this.downloadBtn = document.getElementById('download-csv')
        this.filterField = document.getElementById('release-filter-field');
        this.filterValue = document.getElementById('release-filter-value');
        this.form = document.getElementById('form');
        this.priority = document.getElementById('priority');

        this.releaseForm = document.getElementById('release-admin-offcanvas');
        this.releaseOffCanvas = new bootstrap.Offcanvas(this.releaseForm);

        this.saveBtn = document.getElementById('submit-btn');
        this.shortDesc = document.getElementById('short-desc');
        this.status = document.getElementById('status-select');
        this.supportTeam = document.getElementById('support-team');
        this.ticketNumber = document.getElementById('ticket-number');
        this.ticketType = document.getElementById('ticket-type');
    }


    async init() {
        await this.initialiseAdminReleasesTable();
        this.releaseAdminTabMap = await this.initialiseReleaseAdminTabMap()
        this.chartManager = new ChartManager(this.releaseAdminTabMap);
        this.setupListeners();
    }

     setupListeners() {
        filterFieldListener(this.adminReleasesTable, this.filterField, this.filterValue);

        this.clearFilterBtn.addEventListener('click', () => {
            this.chartManager.triggerDoubleClick('all-releases-type-count', 'All');
        });

        this.downloadBtn.addEventListener('click', () => {
            this.adminReleasesTable.downloadDialog('csv', this.adminReleasesTable);
        });

        this.saveBtn.addEventListener('click', async () => {
            await this.updateRecord();
        });

        this.supportTeam.addEventListener('change', async () => {
            await fetchSupportAgents(this.supportTeam.options[this.supportTeam.selectedIndex].value);
        });

    }

    async initialiseAdminReleasesTable() {
        this.adminReleasesTable = new CustomTabulator(
            '/api/get_paginated/',
            '#all-releases-table',
            {
                'scope': 'all',
                'model': 'release'
            },
            await this.getReleaseAdminColumns(),
            true,
        );

        this.adminReleasesTable.setRowDblClickEventHandler(async (e, row) => {
            await populate_admin_form('release', '/api/release/get-release-ticket/', row);
            this.releaseOffCanvas.show();
            this.saveBtn.disabled = true;
        });

        const tableInstance = this.adminReleasesTable.getTableInstance()
        tableInstance.on('rowDeleted', (row) => handleRowDelete('problem', row));
    }

    async initialiseReleaseAdminTabMap() {
        return {
            'releases-pane': {
                combined: {
                    api: '/api/get-open-by-type-count/',
                    div: 'all-releases-type-count',
                    chart: 'bar',
                    title: 'All Open releases',
                    xLabel: 'release_type',
                    scope: 'all',
                    model: 'Release',
                    ticket_type: 'release',
                    table: this.adminReleasesTable
                },
                category: {
                    api: '/api/get-releases-by-category/',
                    div: 'all-releases-category-count',
                    chart: 'horizontalBar',
                    title: 'Releases by Category',
                    xLabel: 'category',
                    scope: 'all',
                    model: 'Release',
                    ticket_type: 'release',
                    table: this.adminReleasesTable
                },
                status: {
                    api: '/api/get-open-tickets-status-count/',
                    div: 'all-releases-status-count',
                    chart: 'pie',
                    title: 'Open By Status',
                    xLabel: 'status',
                    scope: 'all',
                    model: 'Release',
                    ticket_type: 'release',
                    table: this.adminReleasesTable
                }
            }
        }
    }

    async getReleaseAdminColumns() {
        return [
            {
                title: 'Ticket #',
                field: 'ticket_number',
                hozAlign: 'center',
                headerHozAlign: 'center',
            },
            {
                title: 'Release Type',
                field: 'release_type',
                headerHozAlign: 'center',
            },
            {
                title: 'Release Name',
                field: 'release_name',
                headerHozAlign: 'center',
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
                title: 'Created',
                field: 'created'
            },
        ]
    }
}

const releaseDashboard = new ReleaseAdminDashboard();
await releaseDashboard.init();