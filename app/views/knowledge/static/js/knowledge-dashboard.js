import {CustomTabulator} from '../../../../static/js/table.js';
import {ChartManager} from '../../../../static/js/includes/dashboard-graphs.js';
import {filterFieldListener} from '../../../admin/static/js/config-admin/admin-common-functions.js';

const timezone = Intl.DateTimeFormat().resolvedOptions().timeZone;

export class KnowledgeDashboard {
    constructor() {
        this.myFilterField = document.getElementById('knowledge-filter-field');
        this.myFilterValue = document.getElementById('knowledge-filter-value');
    }

    async init() {
        await this.initialiseTable();
        await this.initialiseTabMap();
        this.chartManager = new ChartManager(this.knowledgeTabMap);
        this.setupListeners();
    }

    async initialiseTable() {
        this.knowledgeTable = new CustomTabulator(
            '/api/get_paginated/',
            '#all-knowledge-table',
            {
                'scope': 'all',
                'model': 'knowledge'
            },
            await this.getKnowledgeColumns(),
            true,
        )

        this.knowledgeTable.setRowDblClickEventHandler((e, row) => {
            const ticketNumber = row.getData().ticket_number;
            window.open(`/ui/knowledge/ticket/?ticket=${ticketNumber}`, '_self');
        })
    }

    setupListeners() {
        this.kbaFilters();
    }

    kbaFilters() {
        document.getElementById('knowledge-clear-filter-btn').addEventListener('click', () => {
            this.chartManager.triggerDoubleClick('knowledge-article-type-count', 'All');
        });

        document.getElementById('knowledge-download-csv').addEventListener('click', () => {
            this.knowledgeTable.downloadDialog('csv', this.knowledgeTable);
        });

        filterFieldListener(this.knowledgeTable, this.myFilterField, this.myFilterValue);
    }

    async initialiseTabMap() {
        this.knowledgeTabMap = {
            'knowledge-tab-pane': {
                article_type: {
                    api: '/api/get-open-by-type-count/',
                    div: 'knowledge-article-type-count',
                    chart: 'bar',
                    title: 'Articles by Type',
                    xLabel: 'article_type',
                    scope: 'all',
                    model: 'Knowledge',
                    ticket_type: 'knowledge',
                    table: this.knowledgeTable
                },
                top_viewed: {
                    api: '/api/knowledge/get-top-viewed-knowledge-count/',
                    div: 'knowledge-top-viewed-count',
                    chart: 'dual-bar',
                    title: 'Top 10 viewed',
                    xLabel: 'top_viewed',
                    scope: 'all',
                    model: 'Knowledge',
                    ticket_type: 'knowledge',
                    table: this.knowledgeTable
                },
                status: {
                    api: '/api/get-open-tickets-status-count/',
                    div: 'knowledge-status-count',
                    chart: 'pie',
                    title: 'All Open By Status',
                    xLabel: 'status',
                    scope: 'all',
                    model: 'Knowledge',
                    ticket_type: 'knowledge',
                    table: this.knowledgeTable
                },
            }
        }
    }

    async getKnowledgeColumns() {
        return [
            {
                title: 'Article #',
                field: 'ticket_number',
                hozAlign: 'center',
                headerHozAlign: 'center',
            },
            {
                title: 'Article Type',
                field: 'article_type'
            },
            {
                title: 'Title',
                field: 'title',
            },
            {
                title: 'Status',
                field: 'status',
                hozAlign: 'center',
                headerHozAlign: 'center',
            },
            {
                title: 'Author',
                field: 'author',
            },
            {
                title: 'Created',
                field: 'created'
            },
            {
                title: 'Times Viewed',
                field: 'times_viewed',
                hozAlign: 'center',
                headerHozAlign: 'center',
                width: 150,
            },
            {
                title: 'Voted Useful',
                field: 'times_useful',
                hozAlign: 'center',
                headerHozAlign: 'center',
                width: 150,
            },
        ]

    }
}

export const knowledgeDashboard = new KnowledgeDashboard();
