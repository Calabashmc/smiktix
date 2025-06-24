import {initialiseGenericTable} from './admin-common-functions.js';
import {CustomTabulator, deleteColumn} from '../../../../../static/js/table.js';
import {showSwal} from '../../../../../static/js/includes/form-classes/form-utils.js';

export class LookupTablesClass {
    constructor() {
        this.addStatusBtn = document.getElementById('add-status-btn');
        this.elements = {
            change: {
                category: {
                    model: 'category',
                    filterBy: 'Change',
                    divId: '#change-category-table',
                    addBtn: document.getElementById('add-change-category-code'),
                    fields: {
                        code: document.getElementById('change-category-code'),
                        comment: document.getElementById('change-category-comment'),
                    }
                },
                changeWindow: {
                    model: 'change_window_lookup',
                    divId: '#change-window-table',
                    addBtn: document.getElementById('add-change-window'),
                    fields: {
                        day: document.getElementById('change-window-day'),
                        start: document.getElementById('change-window-start'),
                        duration: document.getElementById('change-window-duration'),
                        active: document.getElementById('change-window-active')
                    }
                },
                changeRisk: {
                    model: 'change_risk_lookup',
                    divId: '#change-risk-table',
                },
                changeType: {
                    model: 'change_type_lookup',
                    divId: '#change-type-table'
                },
                resolution: {
                    model: 'resolution_lookup',
                    filterBy: 'Change',
                    divId: '#change-resolution-table',
                    addBtn: document.getElementById('add-change-resolution-code'),
                    fields: {
                        code: document.getElementById('change-resolution-code'),
                        comment: document.getElementById('change-resolution-comment'),
                    }
                }

            },
            interaction: {
                category: {
                    model: 'category',
                    filterBy: 'Interaction',
                    divId: '#incident-category-table',
                    addBtn: document.getElementById('add-category-code'),
                    fields: {
                        code: document.getElementById('category-code'),
                        comment: document.getElementById('category-comment'),
                    }
                },
                resolution: {
                    model: 'resolution_lookup',
                    filterBy: 'Interaction',
                    divId: '#incident-resolution-table',
                    addBtn: document.getElementById('add-resolution-code'),
                    fields: {
                        code: document.getElementById('resolution-code'),
                        comment: document.getElementById('resolution-comment'),
                    }
                },
                source: {
                    model: 'source',
                    divId: '#source-table',
                    addBtn: document.getElementById('add-source'),
                    fields: {
                        code: document.getElementById('source'),
                    }
                },
            },
            problem: {
                category: {
                    model: 'category',
                    filterBy: 'Problem',
                    divId: '#problem-category-table',
                    addBtn: document.getElementById('add-problem-category-code'),
                    fields: {
                        code: document.getElementById('problem-category-code'),
                        comment: document.getElementById('problem-category-comment'),
                    }
                },
                resolution: {
                    model: 'resolution_lookup',
                    filterBy: 'Problem',
                    divId: '#problem-resolution-table',
                    addBtn: document.getElementById('add-problem-resolution-code'),
                    fields: {
                        code: document.getElementById('problem-resolution-code'),
                        comment: document.getElementById('problem-resolution-comment'),
                    }
                }
            },
            idea: {
                category: {
                    model: 'category',
                    filterBy: 'Idea',
                    divId: '#idea-category-table',
                    addBtn: document.getElementById('add-idea-category-code'),
                    fields: {
                        code: document.getElementById('idea-category-code'),
                        comment: document.getElementById('idea-category-comment'),
                    }
                },
                resolution: {
                    model: 'resolution_lookup',
                    filterBy: 'Idea',
                    divId: '#idea-resolution-table',
                    addBtn: document.getElementById('add-idea-resolution-code'),
                    fields: {
                        code: document.getElementById('idea-resolution-code'),
                        comment: document.getElementById('idea-resolution-comment'),
                    }
                }
            },
            knowledge: {
                category: {
                    model: 'category',
                    filterBy: 'Knowledge',
                    divId: '#knowledge-category-table',
                    addBtn: document.getElementById('add-knowledge-category-code'),
                    fields: {
                        code: document.getElementById('knowledge-category-code'),
                        comment: document.getElementById('knowledge-category-comment'),
                    }
                },
                kbaType: {
                    model: 'kba_type_lookup',
                    divId: '#kba-types-table',
                    addBtn: document.getElementById('add-kba-type'),
                    fields: {
                        type: document.getElementById('kba-type'),
                    }
                },
            },

            office: {
                addBtn: document.getElementById('location-add-btn'),
                fields: {
                    location: document.getElementById('location'),
                    open_hour: document.getElementById('open-hour'),
                    close_hour: document.getElementById('close-hour'),
                    address: document.getElementById('address'),
                    province: document.getElementById('province'),
                    state: document.getElementById('state'),
                    country_name: document.getElementById('country-name'),
                    timezone: document.getElementById('office-timezone')
                },
            },
        };
        this.deleteColumn = deleteColumn;

        this.model = document.getElementById('model');
        this.status = document.getElementById('status');
    }

    async init() {
        await this.initialiseTables();
        await this.initialiseStatusTable();
        await this.initialiseCategoryTables();
        await this.initialiseResolutionCodesTables();
        this.setupListeners();
    }

    setupListeners() {
        this.addStatusBtn.addEventListener("click", async () => {
            await this.addStatus();
        })
    }

    async addStatus(){
        const modelId = this.model.options[this.model.selectedIndex].value;
        const statusId = this.status.options[this.status.selectedIndex].value;

        const apiArgs = {
            'model-id': modelId,
            'status-id': statusId
        }

        const response = await fetch('/api/lookup/add-status/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(apiArgs),
        });
        const data = await response.json();

        if (!response.ok) {
            console.error('Error:', data['error']);
            await showSwal('Error', data['error'] || 'Record could not be added', 'error');
            return false;
        }else{
            await showSwal('Success', data['message'], 'success');
            const tableInstance = await this.statusLookup.getTableInstance();
            await tableInstance.destroy();
            await this.initialiseStatusTable();
        }
    }

    async initialiseStatusTable() {
       this.statusLookup = await new CustomTabulator(
            '/api/lookup/get_status_lookup/',
            '#status-table',
            null,
            await this.getStatusColumns(),
            false,
            '',
            'name',
        );
    }

    async initialiseTables() {

        // Interation (Incidents and Requests) app default tables
        await initialiseGenericTable({
            model: this.elements.interaction.source.model,
            divId: this.elements.interaction.source.divId,
            columns: this.getSourceColumns(),
            addBtn: this.elements.interaction.source.addBtn,
            fields: this.elements.interaction.source.fields,  // Pass all fields
            buildRecord: (fields) => JSON.stringify({
                source: fields.code.value
            }),
        });


        await initialiseGenericTable({
            model: this.elements.change.changeRisk.model,
            divId: this.elements.change.changeRisk.divId,
            columns: this.getChangeRiskColumns(),
            addBtn: null,
            fields: null,  // Pass all fields
            buildRecord: null
        });

        await initialiseGenericTable({
            model: this.elements.change.changeType.model,
            divId: this.elements.change.changeType.divId,
            columns: this.getChangeTypeColumns(),
            addBtn: null,
            fields: null,  // Pass all fields
            buildRecord: null
        });

        await initialiseGenericTable({
            model: this.elements.change.changeWindow.model,
            divId: this.elements.change.changeWindow.divId,
            columns: this.getChangeWindowsColumns(),
            addBtn: this.elements.change.changeWindow.addBtn,
            fields: this.elements.change.changeWindow.fields,  // Pass all fields
            buildRecord: (fields) => JSON.stringify({
                day: fields.day.value,
                start: fields.start.value,
                duration: fields.duration.value,
                active: fields.active.checked
            }),
        });

        await initialiseGenericTable({
            model: this.elements.knowledge.kbaType.model,
            divId: this.elements.knowledge.kbaType.divId,
            columns: this.getKBATypesColumns(),
            addBtn: this.elements.knowledge.kbaType.addBtn,
            fields: this.elements.knowledge.kbaType.fields,  // Pass all fields
            buildRecord: (fields) => JSON.stringify({
                type: fields.type.value,
            }),
        });

        await initialiseGenericTable({
                model: 'Idea_likelihood_lookup',
                divId: '#idea-likelihood-table',
                columns: this.getIdeaLikelihoodColumns(),
                addBtn: null,
                fields: null,  // Pass all fields
                buildRecord: null
            }
        );

        await initialiseGenericTable({
                model: 'Idea_Benefits_lookup',
                divId: '#idea-benefits-table',
                columns: this.getIdeaBenefitsColumns(),
                addBtn: null,
                fields: null,  // Pass all fields
                buildRecord: null
            }
        );


        await initialiseGenericTable({
            model: 'office_hours',
            divId: '#office-hours-table',
            columns: this.getOfficeHoursColumns(),
            addBtn: this.elements.office.addBtn,
            fields: this.elements.office.fields,  // Pass all fields
            buildRecord: (fields) => JSON.stringify({
                location: fields.location.value,
                open_hour: fields.open_hour.value,
                close_hour: fields.close_hour.value,
                address: fields.address.value,
                province: fields.province.value,
                state: fields.state.value,
                country_name: fields.country_name.value,
                timezone: fields.timezone.value
            }),
        });
    }

    async initialiseCategoryTables() {
        // looks up from this.elements in constructor
        const tableConfigs = [
            this.elements.interaction.category,
            this.elements.problem.category,
            this.elements.change.category,
            this.elements.idea.category,
            this.elements.knowledge.category
        ];

        for (const config of tableConfigs) {
            // loops through tableConfigs above which in turn gives model reference
            await initialiseGenericTable({
                model: config.model,
                filterField: {'field': 'model.name', 'value': config.filterBy,},
                divId: config.divId,
                columns: this.getCategoryColumns(),
                addBtn: config.addBtn,
                fields: config.fields,
                buildRecord: (fields) => JSON.stringify({
                    resolution_code: fields.code.value,
                    resolution_comment: fields.comment.value,
                }),
            });
        }
    }

    async initialiseResolutionCodesTables() {
        const tableConfigs = [
            this.elements.interaction.resolution,
            this.elements.problem.resolution,
            this.elements.change.resolution,
            this.elements.idea.resolution,
        ];

        for (const config of tableConfigs) {
            await initialiseGenericTable({
                model: config.model,
                filterField: {'field': 'model', 'value': config.filterBy,},
                divId: config.divId,
                columns: this.getResolutionCodesColumns(),
                addBtn: config.addBtn,
                fields: config.fields,
                buildRecord: (fields) => JSON.stringify({
                    resolution_code: fields.code.value,
                    resolution_comment: fields.comment.value,
                }),
            });
        }
    }

    getSourceColumns() {
        return [
            {
                title: 'ID',
                headerHozAlign: 'center',
                field: 'id',
                hozAlign: 'center',
                width: 100,
                visible: false,
            },
            {
                title: 'Source',
                headerHozAlign: 'center',
                field: 'source',
                hozAlign: 'left',
                editor: 'input',
            },
            this.deleteColumn
        ];
    }

    getCategoryColumns() {
        return [
            {
                title: 'ID',
                headerHozAlign: 'center',
                field: 'id',
                hozAlign: 'center',
                width: 100,
                visible: false,
            },
            {
                title: 'Category',
                headerHozAlign: 'center',
                field: 'name',
                hozAlign: 'left',
                editor: 'input',
            },
            {
                title: 'Comment',
                headerHozAlign: 'center',
                field: 'comment',
                hozAlign: 'left',
                editor: 'input',
            },
            this.deleteColumn
        ];
    }

    getResolutionCodesColumns() {
        return [
            {
                title: 'ID',
                headerHozAlign: 'center',
                field: 'id',
                hozAlign: 'center',
                width: 100,
                visible: false,
            },
            {
                title: 'Resolution',
                headerHozAlign: 'center',
                field: 'resolution',
                hozAlign: 'left',
                width: 500,
                editor: 'input',
            },
            {
                title: 'Comment',
                headerHozAlign: 'center',
                field: 'comment',
                hozAlign: 'left',
                editor: 'input',
            },
            this.deleteColumn
        ];
    }

    getChangeRiskColumns() {
        return [
            {
                title: 'ID',
                headerHozAlign: 'center',
                field: 'id',
                hozAlign: 'center',
                width: 100,
                visible: false,
            },
            {
                title: 'Risk',
                headerHozAlign: 'center',
                field: 'risk',
                hozAlign: 'center',
                width: 300,
            },
            {
                title: 'Comment',
                headerHozAlign: 'center',
                field: 'comment',
                hozAlign: 'left',
                editor: 'input',
            },
        ];
    }

    getChangeTypeColumns() {
        return [
            {
                title: 'ID',
                headerHozAlign: 'center',
                field: 'id',
                hozAlign: 'center',
                width: 100,
                visible: false,
            },
            {
                title: 'Change Type',
                headerHozAlign: 'center',
                field: 'change_type',
                hozAlign: 'center',
                width: 300,
            },
            {
                title: 'Comment',
                headerHozAlign: 'center',
                field: 'comment',
                hozAlign: 'left',
                editor: 'input',
            },
        ];
    }

    getChangeWindowsColumns() {
        return [
            {
                title: 'ID',
                headerHozAlign: 'center',
                field: 'id',
                hozAlign: 'center',
                width: 100,
                visible: false,
            },
            {
                title: 'Day',
                headerHozAlign: 'center',
                field: 'day',
                hozAlign: 'center',
                width: 300,
            },
            {
                title: 'Start Time',
                headerHozAlign: 'center',
                field: 'start_time',
                hozAlign: 'center',
                editor: 'input',
            },
            {
                title: 'Duration',
                headerHozAlign: 'center',
                field: 'length',
                hozAlign: 'center',
                editor: 'input',
            },
            {
                title: 'Active',
                headerHozAlign: 'center',
                field: 'active',
                formatter: 'tickCross',
                hozAlign: 'center',
                editor: 'tickCross',
            },
            this.deleteColumn
        ];
    }

    getKBATypesColumns() {
        return [
            {
                title: 'ID',
                headerHozAlign: 'center',
                field: 'id',
                hozAlign: 'center',
                width: 100,
                visible: false,
            },
            {
                title: 'Type',
                headerHozAlign: 'center',
                field: 'article_type',
                hozAlign: 'left',
                editor: 'input',
            },
            {
                title: 'Comment',
                headerHozAlign: 'center',
                field: 'comment',
                hozAlign: 'left',
                editor: 'input',
            },
            this.deleteColumn
        ];
    }

    getIdeaBenefitsColumns(){
        return [
            {
                title: 'ID',
                headerHozAlign: 'center',
                field: 'id',
                hozAlign: 'center',
                width: 100,
                visible: false,
            },
            {
                title: 'Benefit',
                headerHozAlign: 'center',
                field: 'benefit',
                hozAlign: 'center',
                width: 300,
            },
            {
                title: 'Comment',
                headerHozAlign: 'center',
                field: 'comment',
                hozAlign: 'left',
                editor: 'input',
            },
        ];
    }

    getIdeaLikelihoodColumns() {
        return [
            {
                title: 'ID',
                headerHozAlign: 'center',
                field: 'id',
                hozAlign: 'center',
                width: 100,
                visible: false,
            },
            {
                title: 'Risk',
                headerHozAlign: 'center',
                field: 'likelihood',
                hozAlign: 'center',
                width: 300,
            },
            {
                title: 'Comment',
                headerHozAlign: 'center',
                field: 'comment',
                hozAlign: 'left',
                editor: 'input',
            },
        ];
    }

    getOfficeHoursColumns() {
        return [
            {
                title: 'ID',
                headerHozAlign: 'center',
                field: 'id',
                hozAlign: 'center',
                width: 100,
                visible: false,
            },
            {
                title: 'Location',
                headerHozAlign: 'center',
                field: 'location',
                hozAlign: 'center',
                width: 300,
            },
            {
                title: 'Open time',
                headerHozAlign: 'center',
                field: 'open_hour',
                hozAlign: 'left',
                editor: 'input',
            },
            {
                title: 'Close time',
                headerHozAlign: 'center',
                field: 'close_hour',
                hozAlign: 'left',
                editor: 'input',
            },
            {
                title: 'Address',
                headerHozAlign: 'center',
                field: 'address',
                hozAlign: 'left',
                editor: 'input',
            },
            {
                title: 'Province',
                headerHozAlign: 'center',
                field: 'province',
                hozAlign: 'left',
                editor: 'input',
            },
            {
                title: 'State',
                headerHozAlign: 'center',
                field: 'state',
                hozAlign: 'left',
                editor: 'input',
            },
            {
                title: 'Country',
                headerHozAlign: 'center',
                field: 'country_name',
                hozAlign: 'left',
                editor: 'input',
            },
            {
                title: 'Timezone',
                headerHozAlign: 'center',
                width: 100,
                field: 'timezone',
                hozAlign: 'left',
                editor: 'input',
            },
            this.deleteColumn,
        ];
    };

    async getStatusColumns() {
        return [
            {
                title: 'ID',
                headerHozAlign: 'center',
                field: 'id',
                hozAlign: 'center',
                width: 100,
                visible: false,
            },
            // {
            //     title: 'Model',
            //     headerHozAlign: 'center',
            //     field: 'name',
            //     hozAlign: 'center',
            //     width: 200,
            // },
            {
                title: 'Status',
                headerHozAlign: 'center',
                field: 'status',
                hozAlign: 'center',
                width: 150,
            },

        ];
    }
}

export const lookupTablesClass = new LookupTablesClass();