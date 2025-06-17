import {CustomTabulator} from '../../../../static/js/table.js';
import {ChartManager} from '../../../../static/js/includes/dashboard-graphs.js';
import {filterFieldListener} from '../../../admin/static/js/config-admin/admin-common-functions.js';

const timezone = Intl.DateTimeFormat().resolvedOptions().timeZone;

export class ReleaseDashboard {
    constructor() {
        this.myFilterField = document.getElementById('my-releases-filter-field');
        this.myFilterValue = document.getElementById('my-releases-filter-value');
        this.teamFilterField = document.getElementById('team-releases-filter-field');
        this.teamFilterValue = document.getElementById('team-releases-filter-value');
        this.allFilterField = document.getElementById('all-releases-filter-field');
        this.allFilterValue = document.getElementById('all-releases-filter-value');
    }

    async init() {
        await this.initialiseReleasesTable();
        this.releaseTabMap = this.initialiseReleaseTabMap();
        this.chartManager = new ChartManager(this.releaseTabMap);
        this.setupListeners();
    }

    setupListeners() {
        this.myFilters();
        this.teamFilters();
        this.allFilters();
    }

    myFilters() {
        document.getElementById('my-clear-filter-btn').addEventListener('click', () => {
            this.chartManager.triggerDoubleClick('my-releases-type-count', 'All');
        });

        document.getElementById('my-tickets-download-csv').addEventListener('click', () => {
            this.myreleasesTable.downloadDialog('csv', this.myreleasesTable);
        });

        filterFieldListener(this.myreleasesTable, this.myFilterField, this.myFilterValue);
    }

    teamFilters() {
        document.getElementById('team-clear-filter-btn').addEventListener('click', () => {
            this.chartManager.triggerDoubleClick('team-releases-type-count', 'All');
        });

        document.getElementById('team-releases-download-csv').addEventListener('click', () => {
            this.teamreleasesTable.downloadDialog('csv', this.teamreleasesTable);
        });

        filterFieldListener(this.teamreleasesTable, this.teamFilterField, this.teamFilterValue);
    }

    allFilters() {
        document.getElementById('all-releases-clear-filter-btn').addEventListener('click', () => {
            this.chartManager.triggerDoubleClick('all-releases-type-count', 'All');
        });

        document.getElementById('all-releases-download-csv').addEventListener('click', () => {
            this.allreleasesTable.downloadDialog('csv', this.allreleasesTable);
        });

        filterFieldListener(this.allreleasesTable, this.allFilterField, this.allFilterValue);
    }

    async initialiseReleasesTable() {
        this.myreleasesTable = new CustomTabulator(
            '/api/get_paginated/',
            '#my-releases-table',
            {
                'scope': 'me',
                'timezone': timezone,
                'model': 'release'
            },
            await this.getReleaseColumns(),
            true,
            'my-filter-info'
        );

        this.myreleasesTable.setRowDblClickEventHandler((e, row) => {
            this.handleTableDblClick(row)
        })

        this.teamreleasesTable = new CustomTabulator(
            '/api/get_paginated/',
            '#team-releases-table',
            {
                'scope': 'team',
                'timezone': timezone,
                'model': 'release'
            },
            await this.getReleaseColumns(),
            true,
            'team-filter-info'
        );

        this.teamreleasesTable.setRowDblClickEventHandler((e, row) => {
            this.handleTableDblClick(row)
        })

        this.allreleasesTable = new CustomTabulator(
            '/api/get_paginated/',
            '#all-releases-table',
            {
                'scope': 'all',
                'timezone': timezone,
                'model': 'release'
            },
            await this.getReleaseColumns(),
            true,
            'all-filter-info'
        );

        this.allreleasesTable.setRowDblClickEventHandler((e, row) => {
            this.handleTableDblClick(row)
        })
    }

    handleTableDblClick(row) {
        const ticketNumber = row.getData().ticket_number;
        window.open(`/ui/release/ticket/?ticket=${ticketNumber}`, '_self');
    }

    initialiseReleaseTabMap() {
        return {
            'my-release-tab-pane': {
                combined: {
                    api: '/api/get-open-by-type-count/',
                    div: 'my-releases-type-count',
                    chart: 'bar',
                    title: 'My Open releases',
                    xLabel: 'release_type',
                    scope: 'me',
                    model: 'Release',
                    ticket_type: 'release',
                    table: this.myreleasesTable
                },
                category: {
                    api: '/api/get-releases-by-category/',
                    div: 'my-releases-category-count',
                    chart: 'horizontalBar',
                    title: 'Releases by Category',
                    xLabel: 'category',
                    scope: 'me',
                    model: 'Release',
                    ticket_type: 'release',
                    table: this.myreleasesTable
                },
                status: {
                    api: '/api/get-open-tickets-status-count/',
                    div: 'my-releases-status-count',
                    chart: 'pie',
                    title: 'Open By Status',
                    xLabel: 'status',
                    scope: 'me',
                    model: 'Release',
                    ticket_type: 'release',
                    table: this.myreleasesTable
                },
            },
            'team-release-tab-pane': {
                combined: {
                    api: '/api/get-open-by-type-count/',
                    div: 'team-releases-type-count',
                    chart: 'bar',
                    title: 'My Teams Open releases',
                    xLabel: 'release_type',
                    scope: 'team',
                    model: 'Release',
                    ticket_type: 'release',
                    table: this.teamreleasesTable
                },
                category: {
                    api: '/api/get-releases-by-category/',
                    div: 'team-releases-category-count',
                    chart: 'horizontalBar',
                    title: 'Releases by Category',
                    xLabel: 'category',
                    scope: 'team',
                    model: 'Release',
                    ticket_type: 'release',
                    table: this.teamreleasesTable
                },
                status: {
                    api: '/api/get-open-tickets-status-count/',
                    div: 'team-releases-status-count',
                    chart: 'pie',
                    title: 'Open By Status',
                    xLabel: 'status',
                    scope: 'team',
                    model: 'Release',
                    ticket_type: 'release',
                    table: this.teamreleasesTable
                },
            },
            'all-release-tab-pane': {
                combined: {
                    api: '/api/get-open-by-type-count/',
                    div: 'all-releases-type-count',
                    chart: 'bar',
                    title: 'All Open releases',
                    xLabel: 'release_type',
                    scope: 'all',
                    model: 'Release',
                    ticket_type: 'release',
                    table: this.allreleasesTable
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
                    table: this.allreleasesTable
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
                    table: this.allreleasesTable
                }
            }
        }
    }

    async getReleaseColumns() {
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

export const releaseDashboard = new ReleaseDashboard();