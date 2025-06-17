import {CustomTabulator} from '../../../../static/js/table.js';
import {ChartManager} from '../../../../static/js/includes/dashboard-graphs.js';
import {filterFieldListener} from '../../../admin/static/js/config-admin/admin-common-functions.js';

const timezone = Intl.DateTimeFormat().resolvedOptions().timeZone;

class ChangeDashboard {
    constructor() {
        this.cabFilterField = document.getElementById('cab-filter-field');
        this.cabFilterValue = document.getElementById('cab-filter-value');
        this.changeFilterField = document.getElementById('change-filter-field');
        this.changeFilterValue = document.getElementById('change-filter-value');
    }

    async init() {
        await this.initialiseChangesTable();
        this.initialiseTabMap();
        this.chartManager = new ChartManager(this.changeTabMap)
        this.setupListeners();
    }

    setupListeners() {
        this.changeFilters();
        this.cabFilters();

    }

    changeFilters() {
        document.getElementById('change-clear-filter-btn').addEventListener('click', () => {
            this.chartManager.triggerDoubleClick('all-change-types-count', 'All');
        });

        document.getElementById('change-tickets-download-csv').addEventListener('click', () => {
            this.allChangeTicketsTable.downloadDialog('csv', this.allChangeTicketsTable);
        });

        filterFieldListener(this.allChangeTicketsTable, this.changeFilterField, this.changeFilterValue);
    }

    cabFilters() {
        document.getElementById('cab-clear-filter-btn').addEventListener('click', () => {
            this.chartManager.triggerDoubleClick('cab-change-type-count', 'All');
        });

        document.getElementById('cab-download-csv').addEventListener('click', () => {
            this.cabTicketsTable.downloadDialog('csv', this.cabTicketsTable);
        });

        filterFieldListener(this.cabTicketsTable, this.cabFilterField, this.cabFilterValue);
    }

    async initialiseChangesTable() {
        this.allChangeTicketsTable = new CustomTabulator(
            '/api/get_paginated/',
            '#all-changes-table',
            {
                'scope': 'all',
                'timezone': timezone,
                'model': 'change'
            },
            await this.getChangeColumns()
        );

        this.allChangeTicketsTable.setRowDblClickEventHandler((e, row) => {
            const ticketNumber = row.getData().ticket_number;
            const changeType = row.getData().change_type.toLowerCase();
            window.open(`/ui/change/ticket/${changeType}/?ticket=${ticketNumber}`, '_self');
        })

        this.cabTicketsTable = new CustomTabulator(
            '/api/get_paginated/',
            '#cab-tickets-table',
            {
                'scope': 'cab',
                'timezone': timezone,
                'model': 'change'
            },
            await this.getCabColumns()
        )

        this.cabTicketsTable.setRowDblClickEventHandler((e, row) => {
            const ticketNumber = row.getData().ticket_number;
            const changeType = row.getData().change_type.toLowerCase();
            window.open(`/ui/change/ticket/${changeType}/?ticket=${ticketNumber}`, '_blank');
        })
    }

    async getChangeColumns() {
        return [
            {
                title: 'Ticket #',
                field: 'ticket_number',
                headerHozAlign: 'center',
                hozAlign: 'center',
            },
            {
                title: 'Change Type',
                field: 'change_type',
                headerHozAlign: 'center',
                hozAlign: 'center',
            },
            {
                title: 'Change Risk',
                field: 'risk',
                headerHozAlign: 'center',
                hozAlign: 'center',
            },
            {
                title: 'Status',
                field: 'status',
                headerHozAlign: 'center',
                hozAlign: 'center',
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
            {
                title: 'Start',
                field: 'start_at',
                headerHozAlign: 'center',
                hozAlign: 'center',
            },
            {
                title: 'End',
                field: 'end_at',
                headerHozAlign: 'center',
                hozAlign: 'center',
            },
        ]
    }

    async getCabColumns() {
        return [
            {
                title: 'Approval Status',
                field: 'cab_approval_status',
                headerHozAlign: 'center',
                hozAlign: 'center',
            },
            {
                title: 'Ticket #',
                field: 'ticket_number',
                headerHozAlign: 'center',
                hozAlign: 'center',
            },
            {
                title: 'Change Type',
                field: 'change_type',
                headerHozAlign: 'center',
                hozAlign: 'center',
            },
            {
                title: 'Change Risk',
                field: 'risk',
                headerHozAlign: 'center',
                hozAlign: 'center',
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
                title: 'Change Date',
                field: 'start_date'
            },
            {
                title: 'Start',
                field: 'start_at',
                headerHozAlign: 'center',
                hozAlign: 'center',
            },
            {
                title: 'End',
                field: 'end_at',
                headerHozAlign: 'center',
                hozAlign: 'center',
            },
        ]
    }

    initialiseTabMap() {
        this.changeTabMap = {
            'all-changes-tab-pane': {
                type: {
                    api: '/api/get-open-by-type-count/',
                    div: 'all-change-types-count',
                    chart: 'bar',
                    title: 'All Change by Type',
                    xLabel: 'change_type',
                    scope: 'all',
                    model: 'Change',
                    ticket_type: 'change',
                    table: this.allChangeTicketsTable
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
                    table: this.allChangeTicketsTable
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
                    table: this.allChangeTicketsTable
                },
            },
            'cab-tab-pane': {
                type: {
                    api: '/api/get-open-by-type-count/',
                    div: 'cab-change-type-count',
                    chart: 'bar',
                    title: 'Change by Type',
                    xLabel: 'change_type',
                    scope: 'cab',
                    model: 'Change',
                    ticket_type: 'change',
                    table: this.cabTicketsTable
                },
                risk: {
                    api: '/api/get-open-tickets-priority-count/',
                    div: 'cab-change-risk-count',
                    chart: 'bar',
                    title: 'All Normal Change by Risk',
                    xLabel: 'risk',
                    scope: 'cab',
                    model: 'Change',
                    ticket_type: 'change',
                    table: this.cabTicketsTable
                },
                status: {
                    api: '/api/change/get-cab-status-count/',
                    div: 'cab-status-count',
                    chart: 'pie',
                    title: 'All By Approval Status',
                    xLabel: 'status',
                    scope: 'cab',
                    model: 'Change',
                    ticket_type: 'change',
                    table: this.cabTicketsTable
                },
            },
        }
    }
}

export const changeDashboard = new ChangeDashboard();