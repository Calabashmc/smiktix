import {CustomTabulator} from '../../../../../static/js/table.js';
import {handleTableEdit} from './table-edit.js';

class SlaConfigClass {
    constructor() {

    }

    async init() {
        await this.initialisePrioritiesTable();
        await this.initialiseMetallicsTable();
        await this.initialiseSlaPauseReasonsTable();
    }

    async initialisePrioritiesTable() {
        // CustomTabulator -> constructor(url, selector, args, columns)
        this.prioritiesTable = new CustomTabulator(
            '/api/get-lookup-records/',
            '#priorities-table',
            {'model': 'Priority_lookup'},
            await this.getPrioritiesColumns(), // Use the dynamically created columns
            '',
            false, // Don't paginate
        );
        const tableInstance = this.prioritiesTable.getTableInstance();
        tableInstance.on('cellEdited', (cell) => handleTableEdit('/api/sla/set-app-default-sla-priority/', cell));
    }

    async getPrioritiesColumns() {
        return [
            {
                title: 'Priority',
                headerHozAlign: 'center',
                field: 'priority',
                hozAlign: 'center',
            },
            {
                title: 'Hours to Respond',
                headerHozAlign: 'center',
                field: 'respond_by',
                hozAlign: 'center',
                editor: 'number',
                editorParams: {
                    min: 0,
                    max: 100,
                    step: 0.25,
                },
            },
            {
                title: 'Hours to Resolve',
                headerHozAlign: 'center',
                field: 'resolve_by',
                hozAlign: 'center',
                editor: 'number',
                editorParams: {
                    min: 0,
                    max: 100,
                    step: 0.25,
                },
            },
            {
                title: '24/7?',
                field: 'twentyfour_seven',
                hozAlign: 'center',
                formatter: 'tickCross',
                headerHozAlign: 'center',
                editor: 'tickCross',
            },
        ];
    }

    async initialiseMetallicsTable() {
        this.metalicsTable = new CustomTabulator(
            '/api/sla/get-metallics/',
            '#metalics-table',
            {},
            await this.getMetallicsColumns(), // Use the dynamically created columns
            false, // Don't paginate
        )
        const tableInstance = this.metalicsTable.getTableInstance();
        tableInstance.on('cellEdited', (cell) => handleTableEdit('/api/sla/set-metallics/', cell));
    }

    async getMetallicsColumns() {
        return [
            {
                title: 'Rating',
                headerHozAlign: 'center',
                width: 100,
                field: 'rating',
                hozAlign: 'center',
            },
            {
                title: 'Importance',
                headerHozAlign: 'center',
                width: 200,
                field: 'importance',
                hozAlign: 'center',
                editor: 'input',
            },
            {
                title: 'Note',
                headerHozAlign: 'center',
                field: 'note',
                editor: 'input',
            },
        ]
    }

    async initialiseSlaPauseReasonsTable() {
        this.slaPauseTable = new CustomTabulator(
            '/api/get_sla_pause_reasons/',
            '#sla-pause-table',
            {},
            await this.getSlaPauseColumns(), // Use the dynamically created columns
            false, // Don't paginate
        )
        const tableInstance = this.slaPauseTable.getTableInstance();
        tableInstance.on('cellEdited', (cell) => handleTableEdit('/api/set_sla_pause_reason/', cell));
    }

    async getSlaPauseColumns() {
        return [
            {
                title: 'ID',
                headerHozAlign: 'center',
                field: 'id',
                hozAlign: 'center',
                width: 100,
            },
            {
                title: 'Reason',
                headerHozAlign: 'center',
                field: 'reason',
                editor: 'input',
            },
        ]
    }
}

export const slaConfigClass = new SlaConfigClass()