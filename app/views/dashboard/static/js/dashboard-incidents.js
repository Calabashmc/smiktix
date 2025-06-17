import {ChartManager} from '../../../../static/js/includes/dashboard-graphs.js';

export class MainDashboardClass {
    constructor() {
        this.dashboardMap = {
            'interactions-tab-pane': {
                interactions: {
                    api: '/api/interaction/get-ticket-stats/',
                    div: 'interactions-graph',
                    chart: 'polar-endAngle',
                    title: 'Interactions',
                    xLabel: 'interactions',
                    scope: 'all',
                    model: 'Interaction',
                    ticket_type: 'Interaction',
                    table: null
                },
                team_load: {
                    api: '/api/get-team-load/',
                    div: 'team-load-graph',
                    chart: 'stacked-horizontal',
                    title: 'Team Load',
                    xLabel: 'team_load',
                    scope: 'all',
                    model: 'Teams',
                    ticket_type: null,
                    table: null
                }
            }
        }
    }

    async init() {
        this.chartManager = new ChartManager(this.dashboardMap);
    }

}