import {CustomTabulator} from '../../../../static/js/table.js';
import {ChartManager} from '../../../../static/js/includes/dashboard-graphs.js';
import {visNetworkClass} from '../../../../static/js/includes/vis-network-class.js';
import {filterFieldListener} from '../../../admin/static/js/config-admin/admin-common-functions.js';

const timezone = Intl.DateTimeFormat().resolvedOptions().timeZone;

class CmdbDashboard {
    constructor() {
        this.networkContainer = document.getElementById('network');
        this.myFilterField = document.getElementById('cmdb-filter-field');
        this.myFilterValue = document.getElementById('cmdb-filter-value');
    }

    async init() {
        await this.initialiseTable();
        this.initialiseTabMap();
        this.chartManager = new ChartManager(this.cmdbTabMap);
        this.setupListeners();

        // use ResizeObserver to detect network container resize to correct dimensions before drawing network
        const resizeObserver = new ResizeObserver(entries => {
            for (let entry of entries) {
                if (entry.contentRect.width > 0 && entry.contentRect.height > 0) {
                    visNetworkClass.drawNetwork(this.networkContainer, null);
                    resizeObserver.disconnect(); // Stop observing after successful draw
                }
            }
        });
        resizeObserver.observe(this.networkContainer);
    }

    setupListeners() {
        this.cmdbFilters();
    }

    cmdbFilters() {
        document.getElementById('cmdb-clear-filter-btn').addEventListener('click', () => {
            this.chartManager.triggerDoubleClick('all-cmdb-importance-count', 'All');
        });

        document.getElementById('cmdb-download-csv').addEventListener('click', () => {
            this.allCisTable.downloadDialog('csv', this.allCisTable);
        });

        filterFieldListener(this.allCisTable, this.myFilterField, this.myFilterValue);
    }

    async initialiseTable() {
        this.allCisTable = new CustomTabulator(
            '/api/get_paginated/',
            '#all-cis-table',
            {
                'scope': 'all',
                'timezone': timezone,
                'model': 'cmdb'
            },
            await this.getCMDBColumns(),
            true,
        )

        this.allCisTable.setRowDblClickEventHandler((e, row) => {
            const ticketNumber = row.getData().ticket_number;
            const ciType = row.getData().ticket_type.toLowerCase();
            window.open(`/ui/cmdb/ticket/${ciType}/?ticket=${ticketNumber}`, '_self');
        })
    }

    initialiseTabMap() {
        this.cmdbTabMap = {
            'cmdb-tab-pane': {
                importance: {
                    api: '/api/get-cmdb-cis-by-importance/',
                    div: 'all-cmdb-importance-count',
                    chart: 'bar',
                    title: "CI's by Importance",
                    xLabel: 'importance',
                    scope: 'all',
                    model: 'cmdb',
                    ticket_type: 'cmdb',
                    table: this.allCisTable
                },
                ticket_type: {
                    api: '/api/get-cmdb-cis-by-ticket-type/',
                    div: 'all-cmdb-ticket-type-count',
                    chart: 'bar',
                    title: "CI's by Type",
                    xLabel: 'category',
                    scope: 'all',
                    model: 'cmdb',
                    ticket_type: 'cmdb',
                    table: this.allCisTable
                },
                category: {
                    api: '/api/get-cmdb-cis-by-category/',
                    div: 'all-cmdb-category-count',
                    chart: 'horizontalBar',
                    title: "CIs by Category",
                    xLabel: 'category',
                    scope: 'all',
                    model: 'cmdb',
                    ticket_type: 'cmdb',
                    table: this.allCisTable
                },
                status: {
                    api: '/api/get-open-tickets-status-count/',
                    div: 'all-status-count',
                    chart: 'pie',
                    title: "CI's By Status",
                    xLabel: 'status',
                    scope: 'all',
                    model: 'cmdb',
                    ticket_type: 'cmdb',
                    table: this.allCisTable
                },
            }
        }
    }

    async getCMDBColumns() {
        return [
            {
                title: "CI #",
                field: "ticket_number",
                headerHozAlign: "center",
                hozAlign: "center",
                width: 150,
            },
            {
                title: "Type",
                field: "ticket_type",
                headerHozAlign: "center",
                hozAlign: "center",
                width: 150,
            },
            {
                title: "Name",
                field: "name"
            },
            {
                title: "Category",
                field: "category",
            },
            {
                title: "Support Team",
                field: "support_team",
            },
            {
                title: "Status",
                field: "status",
            },
            {
                title: "Owned By",
                field: "owned_by",
            },
            {
                title: "Created",
                field: "created"
            },
        ]
    }
}

export const cmdbDashboard = new CmdbDashboard();