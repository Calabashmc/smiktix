import {CustomTabulator} from '../../../../static/js/table.js';
import {ChartManager} from '../../../../static/js/includes/dashboard-graphs.js';
import {filterFieldListener} from '../../../admin/static/js/config-admin/admin-common-functions.js';

const timezone = Intl.DateTimeFormat().resolvedOptions().timeZone;

export class ProblemDashboard {
    constructor() {
        this.myFilterField = document.getElementById('my-problems-filter-field');
        this.myFilterValue = document.getElementById('my-problems-filter-value');
        this.teamFilterField = document.getElementById('team-problems-filter-field');
        this.teamFilterValue = document.getElementById('team-problems-filter-value');
        this.allFilterField = document.getElementById('all-problems-filter-field');
        this.allFilterValue = document.getElementById('all-problems-filter-value');
    }

    async init() {
        await this.initialiseProblemsTable();
        this.initialiseProblemTabMap();
        this.chartManager = new ChartManager(this.problemTabMap);
        this.setupListeners();
    }

    setupListeners() {
        this.myFilters();
        this.teamFilters();
        this.allFilters();
    }

    myFilters() {
        document.getElementById('my-clear-filter-btn').addEventListener('click', () => {
            this.chartManager.triggerDoubleClick('my-problems-type-count', 'All');
        });

        document.getElementById('my-tickets-download-csv').addEventListener('click', () => {
            this.myProblemsTable.downloadDialog('csv', this.myProblemsTable);
        });

        filterFieldListener(this.myProblemsTable, this.myFilterField, this.myFilterValue);
    }

    teamFilters() {
        document.getElementById('team-clear-filter-btn').addEventListener('click', () => {
            this.chartManager.triggerDoubleClick('team-problems-type-count', 'All');
        });

        document.getElementById('team-problems-download-csv').addEventListener('click', () => {
            this.teamProblemsTable.downloadDialog('csv', this.teamProblemsTable);
        });

        filterFieldListener(this.teamProblemsTable, this.teamFilterField, this.teamFilterValue);
    }

    allFilters() {
        document.getElementById('all-problems-clear-filter-btn').addEventListener('click', () => {
            this.chartManager.triggerDoubleClick('all-problems-type-count', 'All');
        });

        document.getElementById('all-problems-download-csv').addEventListener('click', () => {
            this.allProblemsTable.downloadDialog('csv', this.allProblemsTable);
        });

        filterFieldListener(this.allProblemsTable, this.allFilterField, this.allFilterValue);
    }

    async initialiseProblemsTable() {
        this.myProblemsTable = new CustomTabulator(
            '/api/get_paginated/',
            '#my-problems-table',
            {
                'scope': 'me',
                'timezone': timezone,
                'model': 'problem'
            },
            await this.getProblemColumns(),
            true,
            'my-filter-info'
        );

        this.myProblemsTable.setRowDblClickEventHandler((e, row) => {
            this.handleTableDblClick(row)
        })

        this.teamProblemsTable = new CustomTabulator(
            '/api/get_paginated/',
            '#team-problems-table',
            {
                'scope': 'team',
                'timezone': timezone,
                'model': 'problem'
            },
            await this.getProblemColumns(),
            true,
            'team-filter-info'
        );

        this.teamProblemsTable.setRowDblClickEventHandler((e, row) => {
            this.handleTableDblClick(row)
        })

        this.allProblemsTable = new CustomTabulator(
            '/api/get_paginated/',
            '#all-problems-table',
            {
                'scope': 'all',
                'timezone': timezone,
                'model': 'problem'
            },
            await this.getProblemColumns(),
            true,
            'all-filter-info'
        );

        this.allProblemsTable.setRowDblClickEventHandler((e, row) => {
            this.handleTableDblClick(row)
        })
    }

    handleTableDblClick(row) {
        const ticketNumber = row.getData().ticket_number;
        window.open(`/ui/problem/ticket/?ticket=${ticketNumber}`, '_self');
    }

    initialiseProblemTabMap() {
        this.problemTabMap = {
            'my-problem-tab-pane': {
                combined: {
                    api: '/api/get-open-by-type-count/',
                    div: 'my-problems-type-count',
                    chart: 'bar',
                    title: 'My Open Problems',
                    xLabel: 'types',
                    scope: 'me',
                    model: 'Problem',
                    ticket_type: 'Problem',
                    table: this.myProblemsTable
                },
                priority: {
                    api: '/api/get-open-tickets-priority-count/',
                    div: 'my-problems-priority-count',
                    chart: 'bar',
                    title: 'Open by Priority',
                    xLabel: 'priorities',
                    scope: 'me',
                    model: 'Problem',
                    ticket_type: 'Problem',
                    table: this.myProblemsTable
                },
                status: {
                    api: '/api/get-open-tickets-status-count/',
                    div: 'my-problems-status-count',
                    chart: 'pie',
                    title: 'Open By Status',
                    xLabel: 'status',
                    scope: 'me',
                    model: 'Problem',
                    ticket_type: 'Problem',
                    table: this.myProblemsTable
                },
            },
            'team-problem-tab-pane': {
                combined: {
                    api: '/api/get-open-by-type-count/',
                    div: 'team-problems-type-count',
                    chart: 'bar',
                    title: 'My Teams Open Problems',
                    xLabel: 'types',
                    scope: 'team',
                    model: 'Problem',
                    ticket_type: 'Problem',
                    table: this.teamProblemsTable
                },
                priority: {
                    api: '/api/get-open-tickets-priority-count/',
                    div: 'team-problems-priority-count',
                    chart: 'bar',
                    title: 'Open by Priority',
                    xLabel: 'priorities',
                    scope: 'team',
                    model: 'Problem',
                    ticket_type: 'Problem',
                    table: this.teamProblemsTable
                },
                status: {
                    api: '/api/get-open-tickets-status-count/',
                    div: 'team-problems-status-count',
                    chart: 'pie',
                    title: 'Open By Status',
                    xLabel: 'status',
                    scope: 'team',
                    model: 'Problem',
                    ticket_type: 'Problem',
                    table: this.teamProblemsTable
                },
            },
            'all-problem-tab-pane': {
                combined: {
                    api: '/api/get-open-by-type-count/',
                    div: 'all-problems-type-count',
                    chart: 'bar',
                    title: 'All Open Problems',
                    xLabel: 'types',
                    scope: 'all',
                    model: 'Problem',
                    ticket_type: 'Problem',
                    table: this.allProblemsTable
                },
                priority: {
                    api: '/api/get-open-tickets-priority-count/',
                    div: 'all-problems-priority-count',
                    chart: 'bar',
                    title: 'Open by Priority',
                    xLabel: 'priorities',
                    scope: 'all',
                    model: 'Problem',
                    ticket_type: 'Problem',
                    table: this.allProblemsTable
                },
                status: {
                    api: '/api/get-open-tickets-status-count/',
                    div: 'all-problems-status-count',
                    chart: 'pie',
                    title: 'Open By Status',
                    xLabel: 'status',
                    scope: 'all',
                    model: 'Problem',
                    ticket_type: 'Problem',
                    table: this.allProblemsTable
                }
            }
        }
    }

    async getProblemColumns() {
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
        ]
    }
}

export const problemDashboard = new ProblemDashboard();