import {CustomTabulator} from '../../../../../static/js/table.js';
import {ChartManager} from '../../../../../static/js/includes/dashboard-graphs.js';
import {sunEditorClass} from '../../../../../static/js/includes/suneditor-class.js';

const timezone = Intl.DateTimeFormat().resolvedOptions().timeZone;


export class PortalIdeasDashboardClass {
    constructor() {
        this.benefits = document.querySelectorAll('input[type="checkbox"][name="benefits"]');
        this.estimatedCostRadios = document.querySelectorAll('input[type="radio"][name="estimated_cost"]');
        this.category = document.getElementById('offcanvas-category');
        this.details = document.getElementById('offcanvas-details');
        this.estimatedEffortRadios = document.querySelectorAll('input[type="radio"][name="estimated_effort"]');
        this.impacts = document.querySelectorAll('input[type="checkbox"][name="impact"]');
        this.likelihood = document.getElementById('likelihood');
        this.shortDesc = document.getElementById('offcanvas-short-desc');
        this.ticketNumber = document.getElementById('ticket-number');
        this.title = document.getElementById('offcanvas-title');
        this.voteCount = document.getElementById('vote-count');
        this.voteScore = document.getElementById('vote-score');

        sunEditorClass.createSunEditor('offcanvas-current-issue');
        sunEditorClass.createSunEditor('offcanvas-dependencies');
        sunEditorClass.createSunEditor('offcanvas-details');
        sunEditorClass.createSunEditor('offcanvas-risks');
    }

    async init() {
        await this.initialiseIdeasTable();
        await this.initialiseVotableIdeasTable();
        this.initialiseTabMap();
        new ChartManager(this.ideasTabMap)
        this.setupListeners();
    }

    setupListeners() {
        this.allIdeasTable.setRowDblClickEventHandler(async (e, row) => {
            await this.populateTicketDetails(row);
        })

        this.votableIdeasTable.setRowDblClickEventHandler(async (e, row) => {
            await this.populateTicketDetails(row);
        })
    }

    async initialiseIdeasTable() {
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
    }

    async initialiseVotableIdeasTable() {
        this.votableIdeasTable = new CustomTabulator(
            '/api/get_paginated/',
            '#votable-ideas-table',
            {
                'scope': 'votable',
                'timezone': timezone,
                'model': 'idea',
            },
            await this.getIdeasColumns(),
            true,
            this.inPortal
        );
    }

    async getIdeasColumns() {
        return [
            {
                title: 'Idea #',
                field: 'ticket_number',
                hozAlign: 'center',
                headerHozAlign: 'center',
            },
            {
                title: 'Category',
                field: 'category',
            },
            {
                title: 'Short Description',
                field: 'shortDesc'
            },
            {
                title: 'Likelihood',
                headerHozAlign: 'center',
                field: 'likelihood',
                hozAlign: 'center',
            },
            {
                title: 'Status',
                headerHozAlign: 'center',
                field: 'status',
                hozAlign: 'center',
            },
            {
                title: 'Created',
                field: 'created'
            },
            {
                title: 'Votes',
                headerHozAlign: 'center',
                field: 'votes',
                hozAlign: 'center',
                width: 150,
            },
            {
                title: 'Score',
                headerHozAlign: 'center',
                field: 'score',
                hozAlign: 'center',
                width: 150,
            },
        ]
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
                    xLabel: 'status',
                    scope: 'all',
                    model: 'Idea',
                    ticket_type: 'Idea',
                    table: this.allIdeasTable
                },
            },
        }
    }

    async populateTicketDetails(row) {
        const response = await fetch(`/api/idea/get-idea/?ticket-number=${row.getData().ticket_number}`);
        const data = await response.json();

        if (!response.ok) {
            await showSwal('Error', data['error'], 'error');
            return;
        }
        this.portalIdeaForm = new bootstrap.Offcanvas(document.getElementById('portal-idea-offcanvas'));

        this.benefits.forEach((checkbox) => {
            if (data['benefits'].includes(checkbox.value)) {
                checkbox.checked = true;
            }
        });

        this.estimatedEffortRadios.forEach((radio)=>{
            if (data['effort'].includes(radio.value)){
                radio.checked = true;
            }
        });

        this.impacts.forEach((checkbox) => {
            if (data['impacts'].includes(checkbox.value)) {
                checkbox.checked = true;
            }
        });

        this.estimatedCostRadios.forEach((radio)=>{
            if (data['cost'].includes(radio.value)){
                radio.checked = true;
            }
        });


        const detailsEditorInstance = sunEditorClass.sunEditorInstances.get('offcanvas-details');
        if (detailsEditorInstance) {
            detailsEditorInstance.setContents(data['details']);
        } else {
            console.error('SunEditor instance not found');
        }

        const currentIssueEditorInstance = sunEditorClass.sunEditorInstances.get('offcanvas-current-issue');
        if (currentIssueEditorInstance) {
            currentIssueEditorInstance.setContents(data['current-issue']);
        } else {
            console.error('SunEditor instance not found');
        }

        const dependenciesEditorInstance = sunEditorClass.sunEditorInstances.get('offcanvas-dependencies');
        if (dependenciesEditorInstance) {
            dependenciesEditorInstance.setContents(data['dependencies']);
        } else {
            console.error('SunEditor instance not found');
        }

        const risksEditorInstance = sunEditorClass.sunEditorInstances.get('offcanvas-risks');
        if (risksEditorInstance) {
            risksEditorInstance.setContents(data['risks']);
        } else {
            console.error('SunEditor instance not found');
        }

        this.category.innerHTML = data['category'];
        this.likelihood.value = data['likelihood'];
        this.ticketNumber.value = data['ticket-number']
        this.shortDesc.innerHTML = data['short-desc'];
        this.voteCount.value = data['vote-count'];
        this.voteScore.value = data['vote-score'];

        this.portalIdeaForm.show()
    }
}
