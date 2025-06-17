import {CustomTabulator} from '../../../../static/js/table.js';
import {ChartManager} from '../../../../static/js/includes/dashboard-graphs.js';
import {filterFieldListener} from '../../../admin/static/js/config-admin/admin-common-functions.js';

const timezone = Intl.DateTimeFormat().resolvedOptions().timeZone;

export class IdeasDashboard {
    constructor(tableDiv, inPortal) {
        this.inPortal = inPortal;
        this.myFilterField = document.getElementById('ideas-filter-field');
        this.myFilterValue = document.getElementById('ideas-filter-value');
    }

    async init() {
        await this.initialiseTable();
        this.initialiseTabMap();
        this.chartManager = new ChartManager(this.ideasTabMap);
        this.setupListeners();
    }

    setupListeners() {
        this.ideaFilters();
    }

    ideaFilters() {
        document.getElementById('ideas-clear-filter-btn').addEventListener('click', () => {
            this.chartManager.triggerDoubleClick('all-ideas-likelihood-count', 'All');
        });

        document.getElementById('ideas-download-csv').addEventListener('click', () => {
            this.allIdeasTable.downloadDialog('csv', this.allIdeasTable);
        });

        filterFieldListener(this.allIdeasTable, this.myFilterField, this.myFilterValue);
    }

    async initialiseTable() {
        this.allIdeasTable = new CustomTabulator(
            '/api/get_paginated/',
            '#all-ideas-table',
            {
                'scope': 'all',
                'timezone': timezone,
                'model': 'idea',
            },
            await this.getIdeasColumns(),
            true,
            this.inPortal
        );

        this.allIdeasTable.setRowDblClickEventHandler(async (e, row) => {
            // Define your custom behavior for row double click here
            const ticketNumber = row.getData().ticket_number;

            if (this.inPortal) {
                const shortDesc = document.querySelector('#idea-vote-short-desc');
                const category = document.querySelector('#idea-vote-category');
                const created_at = document.querySelector('#created')
                const details = document.querySelector('#idea-vote-details');
                const likelihood = document.querySelector('#likelihood')
                const ideaNumber = document.querySelector('#ticket-number')
                const requester = document.querySelector('#requester')
                const status = document.querySelector('#status');
                const voteCount = document.querySelector('#vote-count');
                const voteScore = document.querySelector('#vote-score')

                const response = await fetch(`/api/idea/get-idea/?ticket_number=${ticketNumber}`);
                const data = await response.json();
                category.innerHTML = data[0]['category'];
                created_at.innerHTML = data[0]['created_at'];
                details.innerHTML = data[0]['details'];
                ideaNumber.value = ticketNumber;
                likelihood.value = data[0]['likelihood'];
                shortDesc.innerHTML = data[0]['short-desc'];
                requester.innerHTML = data[0]['requested_by']
                status.innerHTML = data[0]['status'];
                voteCount.value = data[0]['vote-count'];
                voteScore.value = data[0]['vote-score'];

                const portalIdeaVoteForm = new bootstrap.Offcanvas(document.querySelector('#portal-idea-offcanvas'));

                portalIdeaVoteForm.show()
            } else {
                // model is defined in _header_common from model sent in route
                window.open(`/ui/idea/ticket/?ticket=${ticketNumber}`, '_self');
            }
        });
    }

    initialiseTabMap() {
        this.ideasTabMap = {
            'all-ideas-tab-pane': {
                likelihood: {
                    api: '/api/get-likelihood-count/',
                    div: 'all-ideas-likelihood-count',
                    chart: 'bar',
                    title: 'All Open Ideas',
                    xLabel: 'likelihood',
                    scope: 'all',
                    model: 'Idea',
                    ticket_type: 'Idea',
                    table: this.allIdeasTable
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
                    table: this.allIdeasTable
                },
                status: {
                    api: '/api/get-open-tickets-status-count/',
                    div: 'all-ideas-status-count',
                    chart: 'pie',
                    title: 'All Open By Status',
                    xLabel: "status",
                    scope: "all",
                    model: 'Idea',
                    ticket_type: "Idea",
                    table: this.allIdeasTable
                },
            },

        }
    }

    async getIdeasColumns() {
        return [
            {
                title: "Idea #",
                field: "ticket_number",
                hozAlign: "center",
                headerHozAlign: "center",
            },
            {
                title: "Category",
                field: "category",
            },
            {
                title: "Short Description",
                field: "shortDesc"
            },
            {
                title: "Likelihood",
                headerHozAlign: "center",
                field: "likelihood",
                hozAlign: "center",
            },
            {
                title: "Status",
                headerHozAlign: "center",
                field: "status",
                hozAlign: "center",
            },
            {
                title: "Created",
                field: "created"
            },
            {
                title: "Votes",
                headerHozAlign: "center",
                field: "votes",
                hozAlign: "center",
                width: 150,
            },
            {
                title: "Score",
                headerHozAlign: "center",
                field: "score",
                hozAlign: "center",
                width: 150,
            },
        ]
    }
}

export const ideasDashboard = new IdeasDashboard();
