import {CustomTabulator} from '../../../../../static/js/table.js';
import {showSwal} from '../../../../../static/js/includes/form-classes/form-utils.js';
import {filterFieldListener} from '../../../../admin/static/js/config-admin/admin-common-functions.js';
import {ChartManager} from '../../../../../static/js/includes/dashboard-graphs.js';

export class PortalKbaDashboardClass {
    constructor() {
        this.searchBoxBtn = document.getElementById('kba-search-btn');
        this.searchResults = document.getElementById('search-results');
        this.searchResultsCanvas = document.getElementById('portal-kba-search-results-offcanvas');
        this.searchText = document.getElementById('kba-search');

        // filter fields/buttons
        this.allKbaFilterField = document.getElementById('all-kba-filter-field');
        this.allKbaFilterValue = document.getElementById('all-kba-filter-value');
        this.allKbaClearFilterBtn = document.getElementById('all-kba-clear-filter-btn');
        this.topKbaClearFilterBtn = document.getElementById('top-kba-clear-filter-btn');
        this.topKbaFilterField = document.getElementById('top-kba-filter-field');
        this.topKbaFilterValue = document.getElementById('top-kba-filter-value');

    }

    async init() {
        await this.populateTables();
        this.setUpListeners();
        await this.drawGraphs();
    }

    setUpListeners() {
        filterFieldListener(this.topKbasTable, this.topKbaFilterField, this.topKbaFilterValue);
        filterFieldListener(this.allKbasTable, this.allKbaFilterField, this.allKbaFilterValue);

        this.allKbaClearFilterBtn.addEventListener('click', async () => {
            this.chartManager.triggerDoubleClick('all-kba-article-type-count', 'All');
        });

        this.topKbaClearFilterBtn.addEventListener('click', async () => {
            this.chartManager.triggerDoubleClick('top-kba-article-type-count', 'All');
        });

        this.searchBoxBtn.addEventListener('click', async () => {
            await this.handleSearch();
        })

    }

    async drawGraphs() {
        this.kbaTabMap = await this.initialiseTabMap();
        this.chartManager = new ChartManager(this.kbaTabMap);
    }

    async populateTables() {
        this.topKbasTable = new CustomTabulator(
            '/api/get_paginated/',
            '#top-kbas-table',
            {
                'scope': 'top',
                'model': 'knowledge',
                'limit': 10,
            },
            this.getKnowledgeColumns(),
            true,
        )

        this.topKbasTable.setRowDblClickEventHandler(async (e, row) => {
            this.ticketNumber = row.getData().ticket_number;
            await window.knowledgeOffCanvasForm.showKbaOffcanvasForm(this.ticketNumber);
            await this.incrementTimesViewed();
        })

        this.allKbasTable = new CustomTabulator(
            '/api/get_paginated/',
            '#all-kbas-table',
            {
                'scope': 'published',
                'model': 'knowledge',
            },
            this.getKnowledgeColumns(),
            true,
        )

        this.allKbasTable.setRowDblClickEventHandler(async (e, row) => {
            this.ticketNumber = row.getData().ticket_number;
            await window.knowledgeOffCanvasForm.showKbaOffcanvasForm(this.ticketNumber);
            await this.incrementTimesViewed();
        })
    }


    async incrementTimesViewed() {
        const response = await fetch(`/api/knowledge/increment-knowledge-viewed-count/?ticket_number=${this.ticketNumber}`)
        const data = await response.json();

        if (!response.ok) {
            await showSwal('Error', data['error'])
        } else {
            await this.refreshTables()
        }
    }

    async refreshTables() {
        // need to destroy the table and recreate to show any updates without page refresh
        const kbaTableInstance = this.topKbasTable.getTableInstance();
        kbaTableInstance.destroy();

        const allKbaTableInstance = this.allKbasTable.getTableInstance();
        allKbaTableInstance.destroy();

        await this.populateTables();
    }

    async handleSearch() {
        const searchText = this.searchText.value;
            const response = await fetch('/api/knowledge/search_published_knowledge/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    'search_text': searchText
                })
            })

            const data = await response.json()

            if (!response.ok) {
                await showSwal('Error', data['error'], 'error');
                return;
            }

            // Clear previous results
            this.searchResults.innerHTML = '';

            if (data.length) {
                const ul = document.createElement('ul');

                data.forEach(item => {
                    const li = document.createElement('li');
                    li.innerHTML = `
                                      <strong>Ticket Number:</strong><a href='/knowledge/ticket/?ticket=${item.ticket_number}'> ${item.ticket_number}<br></a>
                                      <strong>Title:</strong> ${item.title}<br>
                                      <strong>Short Descriptions:</strong> ${item.short_desc || 'N/A'}<br>
                                      <hr>
                                    `;
                    ul.appendChild(li);
                });
                this.searchResults.appendChild(ul);
            }

            const searchCanvas = new bootstrap.Offcanvas(this.searchResultsCanvas);
            searchCanvas.show();
    }
    getKnowledgeColumns() {
        return [
            {
                title: 'Ticket #',
                field: 'ticket_number',
                hozAlign: 'center',
                width: 100
            },
            {
                title: 'Article Type',
                headerHozAlign: 'center',
                field: 'article_type',
                hozAlign: 'center',
                width: 150
            },
            {
                title: 'Category',
                headerHozAlign: 'center',
                field: 'article_category',
                hozAlign: 'center',
                width: 200
            },
            {
                title: 'Title',
                headerHozAlign: 'center',
                field: 'title',
                hozAlign: 'center',
                width: 400
            },
            {
                title: 'Summary',
                field: 'short_desc',
                hozAlign: 'left',
            },
            {
                title: 'Times Viewed',
                field: 'times_viewed',
                hozAlign: 'center',
                width: 150,
            },
            {
                title: 'Voted Useful',
                field: 'times_useful',
                hozAlign: 'center',
                width: 150,
            },
        ]
    }

    async initialiseTabMap() {
        return {
            'kbas-top-tab-pane': {
                article_type: {
                    api: '/api/get-open-by-type-count/',
                    div: 'top-kba-article-type-count',
                    chart: 'bar',
                    title: 'Top Published Articles by Type',
                    xLabel: 'article_type',
                    scope: 'top',
                    model: 'Knowledge',
                    ticket_type: 'knowledge',
                    table: this.topKbasTable
                },
                top_viewed: {
                    api: '/api/knowledge/get-top-viewed-knowledge-count/',
                    div: 'top-kba-top-viewed-count',
                    chart: 'dual-bar',
                    title: 'Most viewed',
                    xLabel: 'top_viewed',
                    scope: 'portal',
                    model: 'Knowledge',
                    ticket_type: 'knowledge',
                    table: this.topKbasTable
                },
            },
            'kbas-all-tab-pane': {
                article_type: {
                    api: '/api/get-open-by-type-count/',
                    div: 'all-kba-article-type-count',
                    chart: 'bar',
                    title: 'Published Articles by Type',
                    xLabel: 'article_type',
                    scope: 'published',
                    model: 'Knowledge',
                    ticket_type: 'knowledge',
                    table: this.allKbasTable,
                },
                top_viewed: {
                    api: '/api/knowledge/get-top-viewed-knowledge-count/',
                    div: 'all-kba-top-viewed-count',
                    chart: 'dual-bar',
                    title: 'Most viewed',
                    xLabel: 'top_viewed',
                    scope: 'portal',
                    model: 'Knowledge',
                    ticket_type: 'knowledge',
                    table: this.allKbasTable
                },
            }
        }
    }
}
