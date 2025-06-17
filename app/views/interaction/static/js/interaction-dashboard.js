import {CustomTabulator} from '../../../../static/js/table.js';
import {ChartManager} from '../../../../static/js/includes/dashboard-graphs.js';
import {filterFieldListener} from '../../../admin/static/js/config-admin/admin-common-functions.js';

const timezone = Intl.DateTimeFormat().resolvedOptions().timeZone;

class InteractionDashboard {
    constructor() {
        this.myFilterField = document.getElementById('my-filter-field');
        this.myFilterValue = document.getElementById('my-filter-value');
        this.teamFilterField = document.getElementById('team-filter-field');
        this.teamFilterValue = document.getElementById('team-filter-value');
        this.allFilterField = document.getElementById('all-filter-field');
        this.allFilterValue = document.getElementById('all-filter-value');
    }

    async init() {
        await this.initialiseTicketsTables()
        this.interactionTabMap = await this.initialiseInteractionTabMap()
        this.chartManager = new ChartManager(this.interactionTabMap)
        this.setupListeners();
    }

    setupListeners() {
        this.myFilters();
        this.teamFilters();
        this.allFilters();
    }

    myFilters() {
        document.getElementById('my-clear-filter-btn').addEventListener('click', () => {
            this.chartManager.triggerDoubleClick('my-type-count', 'All');
        });

        document.getElementById('my-tickets-download-csv').addEventListener('click', () => {
            this.myTicketsTable.downloadDialog('csv', this.myTicketsTable);
        });

        filterFieldListener(this.myTicketsTable, this.myFilterField, this.myFilterValue);
    }

    teamFilters() {
        document.getElementById('team-clear-filter-btn').addEventListener('click', () => {
            this.chartManager.triggerDoubleClick('team-type-count', 'All');
        });

        document.getElementById('team-tickets-download-csv').addEventListener('click', () => {
            this.teamTicketsTable.downloadDialog('csv', this.teamTicketsTable);
        });

        filterFieldListener(this.teamTicketsTable, this.teamFilterField, this.teamFilterValue);
    }

    allFilters() {
        document.getElementById('all-clear-filter-btn').addEventListener('click', () => {
            this.chartManager.triggerDoubleClick('all-type-count', 'All');
        });

        document.getElementById('all-tickets-download-csv').addEventListener('click', () => {
            this.allTicketsTable.downloadDialog('csv', this.allTicketsTable);
        });

        filterFieldListener(this.allTicketsTable, this.allFilterField, this.allFilterValue);
    }

    async initialiseTicketsTables() {
        this.myTicketsTable = new CustomTabulator(
            '/api/get_paginated/',
            '#my-tickets-table',
            {
                'scope': 'me',
                'timezone': timezone,
                'model': 'interaction'
            },
            await this.getInteractionColumns(),
            true,
            'filter-info',
        );

        this.teamTicketsTable = new CustomTabulator(
            '/api/get_paginated/',
            '#team-tickets-table',
            {
                'scope': 'team',
                'timezone': timezone,
                'model': 'interaction'
            },
            await this.getInteractionColumns(),
            true,
            'team-filter-info',
        );

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
            'all-filter-info',
        );

        this.myTicketsTable.setRowDblClickEventHandler((e, row) => {
            const ticketNumber = row.getData().ticket_number;
            window.open(`/ui/interaction/ticket/?ticket=${ticketNumber}`, '_self');
        })

        this.teamTicketsTable.setRowDblClickEventHandler((e, row) => {
            const ticketNumber = row.getData().ticket_number;
            window.open(`/ui/interaction/ticket/?ticket=${ticketNumber}`, '_self');
        })

        this.allTicketsTable.setRowDblClickEventHandler((e, row) => {
            const ticketNumber = row.getData().ticket_number;
            window.open(`/ui/interaction/ticket/?ticket=${ticketNumber}`, '_self');
        })
    }

    async getInteractionColumns() {
        return [
            {
                title: 'Ticket #',
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
                title: 'Supported By',
                field: 'supported_by',
            },
            {
                title: 'Support Team',
                field: 'support_team',
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
                title: 'Respond By',
                field: 'respond_by'
            },
            {
                title: 'Resolve By',
                field: 'resolve_by'
            },
            {
                title: 'SLA',
                headerHozAlign: 'center',
                field: '',
                hozAlign: 'center',
                width: 100,
                formatter: 'custom'
            },
        ]
    }

    async initialiseInteractionTabMap() {
        return {
            'my-tab-pane': {
                combined: {
                    api: '/api/get-open-by-type-count/',
                    div: 'my-type-count',
                    chart: 'bar',
                    title: 'My Open Incidents/Requests',
                    xLabel: 'ticket_type',
                    scope: 'me',
                    model: 'Interaction',
                    ticket_type: 'Interaction',
                    table: this.myTicketsTable
                },
                incident: {
                    api: '/api/get-open-tickets-priority-count/',
                    div: 'my-incidents-priority-count',
                    chart: 'bar',
                    title: 'Incidents by Priority',
                    xLabel: 'priorities',
                    scope: 'me',
                    model: 'Interaction',
                    ticket_type: 'Incident',
                    table: this.myTicketsTable
                },
                request: {
                    api: '/api/get-open-tickets-priority-count/',
                    div: 'my-requests-priority-count',
                    chart: 'bar',
                    title: 'Requests by Priority',
                    xLabel: 'priorities',
                    scope: 'me',
                    model: 'Interaction',
                    ticket_type: 'Request',
                    table: this.myTicketsTable
                },
                status: {
                    api: '/api/get-open-tickets-status-count/',
                    div: 'my-status-count',
                    chart: 'pie',
                    title: 'Open By Status',
                    xLabel: 'status',
                    scope: 'me',
                    model: 'Interaction',
                    ticket_type: 'Interaction',
                    table: this.myTicketsTable
                },
            },
            'team-tab-pane': {
                combined: {
                    api: '/api/get-open-by-type-count/',
                    div: 'team-type-count',
                    chart: 'bar',
                    title: 'My Teams Open Incidents/Requests',
                    xLabel: 'ticket_type',
                    scope: 'team',
                    model: 'Interaction',
                    ticket_type: 'Interaction',
                    table: this.teamTicketsTable
                },
                incident: {
                    api: '/api/get-open-tickets-priority-count/',
                    div: 'team-incidents-priority-count',
                    chart: 'bar',
                    title: 'Open Incidents',
                    xLabel: 'priorities',
                    scope: 'team',
                    model: 'Interaction',
                    ticket_type: 'Incident',
                    table: this.teamTicketsTable
                },
                request: {
                    api: '/api/get-open-tickets-priority-count/',
                    div: 'team-requests-priority-count',
                    chart: 'bar',
                    title: 'Open Requests',
                    xLabel: 'priorities',
                    scope: 'team',
                    model: 'Interaction',
                    ticket_type: 'Request',
                    table: this.teamTicketsTable
                },
                status: {
                    api: '/api/get-open-tickets-status-count/',
                    div: 'team-status-count',
                    chart: 'pie',
                    title: 'Open By Status',
                    xLabel: 'status',
                    scope: 'team',
                    model: 'Interaction',
                    ticket_type: 'Interaction',
                    table: this.teamTicketsTable
                }
            },
            'all-tab-pane': {
                combined: {
                    api: '/api/get-open-by-type-count/',
                    div: 'all-type-count',
                    chart: 'bar',
                    title: 'All Open Incidents/Requests',
                    xLabel: 'ticket_type',
                    scope: 'all',
                    model: 'Interaction',
                    ticket_type: 'Interaction',
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
                    ticket_type: 'Interaction',
                    table: this.allTicketsTable
                },
            }
        }
    }
}

export const interactionDashboard = new InteractionDashboard();