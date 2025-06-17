import {showSwal} from '../../../../static/js/includes/form-classes/form-utils.js';
import {deleteColumn} from '../../../../static/js/table.js';
import {CustomTabulator} from '../../../../static/js/table.js';
import {ChartManager} from '../../../../static/js/includes/dashboard-graphs.js';
import {filterFieldListener, populate_admin_form} from './config-admin/admin-common-functions.js';
import {cmdbDashboard} from '../../../cmdb/static/js/cmdb-dashboard.js';
import {initaliseTomSelectFields} from '../../../../static/js/includes/tom-select.js';
import {handleRowDelete} from './config-admin/table-edit.js';


const timezone = Intl.DateTimeFormat().resolvedOptions().timeZone;

class CmdbAdminDashboard {
    constructor() {
        this.assetTag = document.getElementById('asset-tag');
        this.brand = document.getElementById('brand');
        this.category = document.getElementById('category-id');
        this.clearFilterBtn = document.getElementById('clear-filter-btn');
        this.createdBy = document.getElementById('created-by');

        // off canvas forms
        this.cmdbOffCanvasForm = document.getElementById('cmdb-admin-offcanvas');
        this.cmdbOffCanvas = new bootstrap.Offcanvas(this.cmdbOffCanvasForm);

        this.disposeDate = document.getElementById('disposed-date');
        this.downloadCsvBtn = document.getElementById('download-csv');
        this.endLifeDate = document.getElementById('end-life-date');
        this.filterField = document.getElementById('cmdb-filter-field');
        this.filterValue = document.getElementById('cmdb-filter-value');
        this.form = document.getElementById('form');
        this.importance = document.getElementById('importance');
        this.installDate = document.getElementById('install-date');
        this.location = document.getElementById('location');
        this.licenceCount = document.getElementById('licence-count');
        this.licenceExpire = document.getElementById('licence-expiration-date');
        this.name = document.getElementById('name');
        this.obtainedDate = document.getElementById('obtained-date');
        this.replacedDate = document.getElementById('replacement-date');
        this.replacedWith = document.getElementById('replacement-node');
        this.requestedBy = document.getElementById('requested-by');
        this.retiredDate = document.getElementById('retirement-date');
        this.saveBtn = document.getElementById('submit-btn');
        this.serialNumber = document.getElementById('serial-number');
        this.shortDesc = document.getElementById('short-desc');
        this.status = document.getElementById('status-select');
        this.supportEndDate = document.getElementById('support-ends-date');
        this.supportTeam = document.getElementById('support-team');
        this.supportType = document.getElementById('support-type');
        this.ticketType = document.getElementById('ticket-type');
        this.ticketNumber = document.getElementById('ticket-number');
        this.vendor = document.getElementById('vendor');
        this.version = document.getElementById('version');
        this.warrantyExpire = document.getElementById('warranty-expiration-date');
    }

    async init() {
        await this.initialiseAdminCmdbTable();
        await this.initialiseTabMap();
        this.chartManager = new ChartManager(this.cmdbTabMap);
        // initaliseTomSelectFields();
        this.setupListeners();
    }

    setupListeners() {
        filterFieldListener(this.adminCmdbTable, this.filterField, this.filterValue);

        this.clearFilterBtn.addEventListener('click', () => {
            this.chartManager.triggerDoubleClick('all-cmdb-importance-count', 'All');
        });

        this.downloadCsvBtn.addEventListener('click', () => {
            this.adminCmdbTable.downloadDialog('csv', this.adminCmdbTable);
        });

        this.form.addEventListener('input', () => {
            this.saveBtn.disabled = false; // Enable the button
        });

        this.saveBtn.addEventListener('click', async () => {
            await this.updateRecord()
        });
    }

    // Function to initialize the adminTicketsTable
    async initialiseAdminCmdbTable() {
        this.adminCmdbTable = new CustomTabulator(
            '/api/get_paginated/',
            '#all-cmdb-table',
            {
                'scope': 'all',
                'timezone': timezone,
                'model': 'cmdb',
            },
            await this.getCmdbColumns(),
            true,
            'filter-info'
        );

        this.tableInstance = this.adminCmdbTable.getTableInstance();

        this.adminCmdbTable.setRowDblClickEventHandler(async (e, row) => {
            await populate_admin_form('cmdb', '/api/get-cmdb-ticket/', row);
            this.cmdbOffCanvas.show();
            this.saveBtn.disabled = true;
        });

        this.tableInstance.on('rowDeleted', (row) => handleRowDelete('cmdb', row));
    }

    async updateRecord() {
        const response = await fetch('/api/update_table_row/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                'asset_tag': this.assetTag.value,
                'brand': this.brand.value,
                'category_id': this.category.value,
                'created_by_id': this.createdBy.options[this.createdBy.selectedIndex].value,
                'disposed_date': this.disposeDate.value,
                'end_life_date': this.endLifeDate.value,
                'importance_id': this.importance.value,
                'install_date': this.installDate.value,
                'licence_count': this.licenceCount.value,
                'licence_expiration_date': this.licenceExpire.value,
                'location': this.location.value,
                'model': 'CmdbConfigurationItem',
                'name': this.name.value,
                'obtained_date': this.obtainedDate.value,
                'replacement_date': this.replacedDate.value,
                'replacement_node': this.replacedWith.value,
                'requester_id': this.requestedBy.value,
                'retirement_date': this.retiredDate.value,
                'serial_number': this.serialNumber.value,
                'short_desc': this.shortDesc.value,
                'status': this.status.value,
                'support_ends': this.supportEndDate.value,
                'support_team_id': this.supportTeam.value,
                'support_type': this.supportType.value,
                'ticket_number': this.ticketNumber.value,
                'ticket-type': this.ticketType.value,
                'vendor_id': this.vendor.value,
                'version': this.version.value,
                'warranty_expires': this.warrantyExpire.value
            })
        })

        if (response.ok) {
            await showSwal('Success', 'Ticket Updated', 'success');
            this.cmdbOffCanvas.hide();
            this.tableInstance.destroy();
            await this.initialiseAdminCmdbTable();
        }
    }

    // Function to initialize the interactionTabMap
    async initialiseTabMap() {
        this.cmdbTabMap = {
            'cmdb-tab-pane': {
                importance: {
                    api: '/api/get-cmdb-cis-by-importance/',
                    div: 'all-cmdb-importance-count',
                    chart: 'bar',
                    title: 'CI\'s by Importance',
                    xLabel: 'importance',
                    scope: 'all',
                    model: 'cmdb',
                    ticket_type: 'cmdb',
                    table: this.adminCmdbTable
                },
                category: {
                    api: '/api/get-cmdb-cis-by-category/',
                    div: 'all-cmdb-category-count',
                    chart: 'horizontalBar',
                    title: 'CI\'s by Category',
                    xLabel: 'category',
                    scope: 'all',
                    model: 'cmdb',
                    ticket_type: 'cmdb',
                    table: this.adminCmdbTable
                },
                status: {
                    api: '/api/get-open-tickets-status-count/',
                    div: 'all-status-count',
                    chart: 'pie',
                    title: 'CI\'s By Status',
                    xLabel: 'status',
                    scope: 'all',
                    model: 'cmdb',
                    ticket_type: 'cmdb',
                    table: this.adminCmdbTable
                },
            }
        }
    }


    async getCmdbColumns() {
        this.cmdbColumns = await cmdbDashboard.getCMDBColumns();
        this.cmdbColumns.push(deleteColumn)
        return this.cmdbColumns
    }

}

const cmdbAdminDashboard = new CmdbAdminDashboard();
await cmdbAdminDashboard.init();