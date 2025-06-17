import {CustomTabulator} from '../../../../../static/js/table.js';
import {ChartManager} from '../../../../../static/js/includes/dashboard-graphs.js';
import {StatusClass} from '../../../../../static/js/includes/form-classes/status.js';


const timezone = Intl.DateTimeFormat().resolvedOptions().timeZone;


export class InteractionDashboard {
    constructor() {
        this.createdAt = document.getElementById('created-at');
        this.lastUpdated = document.getElementById('last-updated')
        this.offCanvasTitle = document.getElementById('offcanvas-title');
        this.resolveBy = document.getElementById('resolve-by');
        this.respondBy = document.getElementById('respond-by');
        this.shortDesc = document.getElementById('short-desc-div');
        this.statusSelect = document.getElementById('status');
        this.steps = [
            {id: 'new', label: 'New', icon: 'file-earmark-plus', allowedNext: [], tabs: []},
            {id: 'in-progress', label: 'In Progress', icon: 'pencil-square', allowedNext: [], tabs: []},
            {id: 'resolved', label: 'Resolved', icon: 'tools', allowedNext: [], tabs: []},
            {id: 'review', label: 'Review', icon: 'bootstrap-reboot', allowedNext: [], tabs: []},
            {id: 'closed', label: 'Closed', icon: 'archive-fill', allowedNext: [], tabs: []},
        ];
        this.supportAgent = document.getElementById('support-agent');
        this.supportTeam = document.getElementById('support-team');
        this.ticketDetails = document.getElementById('ticket-details');
        this.ticketPriority = document.getElementById('ticket-priority');

    }

    async init() {
        await this.initialiseMyTicketsTable()
        this.interactionTabMap = await this.initialiseMyInteractionTabMap()
        new ChartManager(this.interactionTabMap)
        this.setupListeners();
    }

    setupListeners() {
        this.myTicketsTable.setRowDblClickEventHandler(async (e, row) => {
            this.portalTicketForm = new bootstrap.Offcanvas(document.getElementById('portal-ticket-offcanvas'));
            this.portalTicketForm.show()

            await this.populateTicketDetails(row);
        })
    }

    async initialiseMyTicketsTable() {
        this.myTicketsTable = new CustomTabulator(
            '/api/get_paginated/',
            '#my-tickets-table',
            {
                'scope': 'portal',
                'timezone': timezone,
                'model': 'interaction'
            },
            this.getInteractionColumns()
        );
    }

    getInteractionColumns() {
        return [
            {
                title: 'Ticket #',
                field: 'ticket_number',
                hozAlign: 'center',
                width: 100,
                headerFilter: 'input'
            },
            {
                title: 'Type',
                field: 'ticket_type',
                width: 150,
                headerFilter: 'list',
                headerFilterParams: {valuesLookup: true, clearable: true}
            },
            {
                title: 'Priority',
                field: 'priority',
                hozAlign: 'center',
                width: 100,
                headerFilter: 'list',
                headerFilterParams: {valuesLookup: true, clearable: true}
            },
            {
                title: 'Status',
                field: 'status',
                hozAlign: 'center',
                width: 150,
                headerFilter: 'list',
                headerFilterParams: {valuesLookup: true, clearable: true}
            },
            {
                title: 'Supported By',
                field: 'supported_by',
                width: 250,
                headerFilter: 'input',
            },
            {
                title: 'Short Description',
                field: 'shortDesc'
            },
            {
                title: 'Created',
                field: 'created',
                width: 150,
            },
            {
                title: 'Respond By',
                field: 'respond_by',
                width: 150,
            },
            {
                title: 'Resolve By',
                field: 'resolve_by',
                width: 150,
            },
            {
                title: 'SLA',
                field: '',
                hozAlign: 'center',
                width: 80,
                formatter: 'custom'
            }
        ]
    }

    async initialiseMyInteractionTabMap() {
        return {
            'portal-my-tickets-tab-pane': {
                combined: {
                    api: '/api/get-open-by-type-count/',
                    div: 'my-type-count',
                    chart: 'bar',
                    title: 'My Open Incidents/Requests',
                    xLabel: 'ticket_type',
                    scope: 'portal',
                    model: 'Interaction',
                    ticket_type: 'Interaction',
                    table: this.myTicketsTable
                },
                incident: {
                    api: '/api/get-open-tickets-priority-count/',
                    div: 'my-incidents-priority-count',
                    chart: 'bar',
                    title: 'Open Incidents by Priority',
                    xLabel: 'priorities',
                    scope: 'portal',
                    model: 'Interaction',
                    ticket_type: 'Incident',
                    table: this.myTicketsTable
                },
                request: {
                    api: '/api/get-open-tickets-priority-count/',
                    div: 'my-requests-priority-count',
                    chart: 'bar',
                    title: 'Open Requests by Priority',
                    xLabel: 'priorities',
                    scope: 'portal',
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
                    scope: 'portal',
                    model: 'Interaction',
                    ticket_type: 'Interaction',
                    table: this.myTicketsTable
                },
            },
        }
    }

    async populateTicketDetails(row) {
        const response = await fetch(`/api/interaction/get-incident-ticket/?ticket-number=${row.getData().ticket_number}`);
        const data = await response.json();

        if (!response.ok) {
            await showSwal('Error', data['error'], 'error');
            return;
        }

        const pValues = {
            1: 'text-primary',
            2: 'text-warning',
            3: 'text-primary',
            4: 'text-info',
            5: 'text-success',
        }

        this.ticketPriority.classList.add('text-center', 'h1');
        this.ticketPriority.classList.add(`${pValues[data.priority[1]]}`);

        this.offCanvasTitle.innerHTML = `Ticket ${row.getData().ticket_number}`;
        this.statusSelect.value = data['status-select'];
        this.supportAgent.innerHTML = data['support-agent'];
        this.supportTeam.innerHTML = data['support-team'];
        this.ticketPriority.innerHTML = data['priority'];
        this.respondBy.innerHTML = data['respond-by'];
        this.resolveBy.innerHTML = data['resolve-by'];
        this.createdAt.innerHTML = data['created-at'];
        this.lastUpdated.innerHTML = data['last-updated']
        this.shortDesc.innerHTML = data['short-desc']
        this.ticketDetails.innerHTML = data['details']

        const statusClass = new StatusClass(this.steps);
        statusClass.init();
    }
}

