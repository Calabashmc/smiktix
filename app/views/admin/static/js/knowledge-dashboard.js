import {showSwal} from '../../../../static/js/includes/form-classes/form-utils.js';
import {deleteColumn} from '../../../../static/js/table.js';
import {CustomTabulator} from '../../../../static/js/table.js';
import {ChartManager} from '../../../../static/js/includes/dashboard-graphs.js';
import {filterFieldListener, populate_admin_form} from './config-admin/admin-common-functions.js';
import {knowledgeDashboard} from '../../../knowledge/static/js/knowledge-dashboard.js';
import {initaliseTomSelectFields} from '../../../../static/js/includes/tom-select.js';

const timezone = Intl.DateTimeFormat().resolvedOptions().timeZone;

class KnowledgeAdminDashboard {
    constructor() {
        this.articleType = document.getElementById('article-type');
        this.authorId = document.getElementById('author-id');
        this.categoryId = document.getElementById('category-id');
        this.clearFilterBtn = document.getElementById('clear-filter-btn');
        this.createdAt = document.getElementById('created-at');
        this.createdBy = document.getElementById('created-by');
        this.details = document.getElementById('details');
        this.downloadBtn = document.getElementById('download-csv')
        this.expiresAt = document.getElementById('expires-at');
        this.filterField = document.getElementById('knowledge-filter-field');
        this.filterValue = document.getElementById('knowledge-filter-value');
        this.form = document.getElementById('form');
        this.knowledgeForm = document.getElementById('knowledge-admin-offcanvas');
        this.knowledgeOffCanvas = new bootstrap.Offcanvas(this.knowledgeForm);
        this.publishedAt = document.getElementById('published-at');
        this.reviewAt = document.getElementById('review-at');
        this.saveBtn = document.getElementById('submit-btn');
        this.shortDesc = document.getElementById('short-desc');
        this.status = document.getElementById('status-select');
        this.ticketNumber = document.getElementById('ticket-number');
        this.title = document.getElementById('title');
        this.ticketType = document.getElementById('ticket-type');
    }

    async init() {
        await this.initialiseAdminKnowledgeTable();
        await this.initialiseTabMap();
        this.chartManager = new ChartManager(this.knowledgeTabMap);
        // initaliseTomSelectFields();
        this.setupListeners();
    }

    setupListeners() {
        filterFieldListener(this.adminKnowledgeTable, this.filterField, this.filterValue);

        this.clearFilterBtn.addEventListener('click', () => {
            this.chartManager.triggerDoubleClick('knowledge-article-type-count', 'All');
        });

        this.downloadBtn.addEventListener('click', () => {
            this.adminKnowledgeTable.downloadDialog('csv', this.adminKnowledgeTable);
        });

        this.form.addEventListener('input', () => {
            this.saveBtn.disabled = false; // Enable the button
        });

        this.saveBtn.addEventListener('click', async () => {
            await this.updateRecord()
        });
    }

    // Function to initialize the adminTicketsTable
    async initialiseAdminKnowledgeTable() {
        this.adminKnowledgeTable = new CustomTabulator(
            '/api/get_paginated/',
            '#all-knowledge-table',
            {
                'scope': 'all',
                'timezone': timezone,
                'model': 'knowledge'
            },
            await this.getKnowledgeColumns(),
            true
        );

        this.tableInstance = this.adminKnowledgeTable.getTableInstance();
        this.tableInstance.on('rowDblClick', async (e, row) => {
            await populate_admin_form('Knowledge', '/api/get-knowledge-ticket/', row);
            this.knowledgeOffCanvas.show()
            this.saveBtn.disabled = true;
        });
    }

    async updateRecord() {
        const response = await fetch('/api/update_table_row/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                'article-type': this.articleType.value,
                'author-id': this.authorId.value,
                'category-id': this.categoryId.value,
                'created-by': this.createdBy.value,
                'expires-at': this.expiresAt.value,
                'model': 'Knowledge',
                'published-at': this.publishedAt.value,
                'review-at': this.reviewAt.value,
                'short-desc': this.shortDesc.value,
                'status': this.status.value,
                'ticket-number': this.ticketNumber.value,
                'ticket-type': this.ticketType.value,
            })
        })

        if (response.ok) {
            await showSwal('Success', 'Ticket Updated', 'success');
            this.knowledgeOffCanvas.hide();
            this.tableInstance.destroy();
            await this.initialiseAdminKnowledgeTable();
        }
    }


    // Function to initialize the interactionTabMap
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
                    table: this.adminKnowledgeTable
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
                    table: this.adminKnowledgeTable
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
                    table: this.adminKnowledgeTable
                },
            }
        }
    }

    async getKnowledgeColumns() {
        this.knowledgeColumns = await knowledgeDashboard.getKnowledgeColumns();
        this.knowledgeColumns.push(deleteColumn)
        return this.knowledgeColumns
    }

}

const knowledgeAdminDashboard = new KnowledgeAdminDashboard();
await knowledgeAdminDashboard.init();