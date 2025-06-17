import {deleteColumn, CustomTabulator} from '../../../../static/js/table.js';
import {ChartManager} from '../../../../static/js/includes/dashboard-graphs.js';
import {formValidationListener} from '../../../../static/js/includes/validate-form.js';
import {
    setTomSelectById,
    filterFieldListener,
    initialiseGenericTable
} from './config-admin/admin-common-functions.js';
import {hideFormButtons, showSwal} from '../../../../static/js/includes/form-classes/form-utils.js';
import {initaliseTomSelectFields} from '../../../../static/js/includes/tom-select.js';


function toolTips() {
    // Initialize Bootstrap tooltips
    document.querySelectorAll('[data-bs-toggle=\'tooltip\']').forEach(tooltipTriggerEl => {
        new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

toolTips()

const timezone = Intl.DateTimeFormat().resolvedOptions().timeZone;


export class UserDashboard {
    constructor() {
        this.addUserBtn = document.getElementById('add-user');

        this.addUserForm = document.getElementById('add-user-offcanvas');
        this.addUserOffcanvas = new bootstrap.Offcanvas(this.addUserForm);

        this.cancelAddUserBtn = document.getElementById('cancel-btn');
        this.departmentsDownloadCsvBtn = document.getElementById('departments-download-csv');

        this.elements = {
            team: {
                addBtn: document.getElementById('add-team-btn'),
                fields: {
                    name: document.getElementById('team-value'),
                }
            },
            department: {
                addBtn: document.getElementById('add-department-btn'),
                fields: {
                    name: document.getElementById('department-value'),
                }
            },
            role: {
                addBtn: document.getElementById('add-role-btn'),
                fields: {
                    name: document.getElementById('role-value'),
                }
            },
        };

        this.importCSVBtn = document.getElementById('import-csv-btn');
        this.rolesDownloadCsvBtn = document.getElementById('roles-download-csv');
        this.submitAddUserBtn = document.getElementById('submit-btn');
        this.teamDownloadCsvBtn = document.getElementById('teams-download-csv');
        this.userClearFilterBtn = document.getElementById('user-clear-filter-btn');
        this.userDownloadCsvBtn = document.getElementById('user-download-csv');
        this.userFilterField = document.getElementById('filter-field');
        this.userFilterValue = document.getElementById('filter-value');

        //  Add user form elements
        this.active = document.getElementById('active');
        this.avatar = document.getElementById('avatar');
        this.firstName = document.getElementById('first-name');
        this.lastName = document.getElementById('last-name');
        this.userName = document.getElementById('username');
        this.fullName = document.getElementById('full-name');
        this.role = document.getElementById('role');

        this.email = document.getElementById('email');
        this.phone = document.getElementById('phone');
        this.department = document.getElementById('department');
        this.team = document.getElementById('team');
        this.manager = document.getElementById('manager');
        this.offCanvasTitle = document.getElementById('offcanvas-title')
        this.occupation = document.getElementById('occupation');
        this.password = document.getElementById('password');
        this.passwordConfirm = document.getElementById('confirm-password');
        this.passwordRevealBtn = document.getElementById('password-prepend');

        this.userAvatar = document.getElementById('user-avatar');
        this.userId = document.getElementById('user-id');
    }

    async init() {
        await initaliseTomSelectFields();
        await this.initialiseTables();
        this.setupListeners();
        this.setEventHandlers();
        this.initializeInteractionMap();
        this.chartManager = new ChartManager(this.interactionTabMap);
        formValidationListener(); // validate form before saving
    }

    async initialiseTables() {
        // CustomTabulator -> constructor(url, selector, args, columns)
        this.adminUsersTable = new CustomTabulator(
            '/api/get_paginated/',
            '#users-table',
            {
                scope: 'all',
                timezone: timezone,
                model: 'users'
            },
            await this.getUserColumns(),
            true
        );

        this.adminTeamsTable = await initialiseGenericTable({
            model: 'team',
            divId: '#teams-table',
            columns: this.getTeamColumns(),
            addBtn: this.elements.team.addBtn,
            fields: this.elements.team.fields,  // Pass all fields
            buildRecord: (fields) => JSON.stringify({
                name: fields.name.value
            }),
        });

        this.adminDepartmentsTable = await initialiseGenericTable({
            model: 'department',
            divId: '#departments-table',
            columns: this.getDepartmentColumns(),
            addBtn: this.elements.department.addBtn,
            fields: this.elements.department.fields,  // Pass all fields
            buildRecord: (fields) => JSON.stringify({
                name: fields.name.value
            }),
        });

        this.adminRolesTable = await initialiseGenericTable({
            model: 'role',
            divId: '#roles-table',
            columns: this.getRoleColumns(),
            addBtn: this.elements.role.addBtn,
            fields: this.elements.role.fields,  // Pass all fields
            buildRecord: (fields) => JSON.stringify({
                name: fields.name.value
            }),
        });
    }

    setupListeners() {
        filterFieldListener(this.adminUsersTable, this.userFilterField, this.userFilterValue);
        // User tab and add user form
        this.addUserBtn.addEventListener('click', () => {
            this.offCanvasTitle.innerHTML = 'Add New User'
            this.addUserOffcanvas.show();
        });

        this.cancelAddUserBtn.addEventListener('click', async () => {
            this.addUserOffcanvas.hide();
        });

        this.importCSVBtn.addEventListener('click', async () => {
            await this.csvImport()
        })
        this.passwordRevealBtn.addEventListener('click', () => {
            this.password.type = this.password.type === 'password' ? 'text' : 'password';
            this.passwordConfirm.type = this.passwordConfirm.type === 'password' ? 'text' : 'password';
        });

        this.submitAddUserBtn.addEventListener('click', async () => {
            await this.addUser();
        });

        this.userClearFilterBtn.addEventListener('click', () => {
            this.chartManager.triggerDoubleClick('all-users-status-count', 'All');
        });

        this.userDownloadCsvBtn.addEventListener('click', () => {
            this.adminUsersTable.downloadDialog('csv', this.adminUsersTable);
        });


        // teams tab
        this.teamDownloadCsvBtn.addEventListener('click', () => {
            this.adminTeamsTable.downloadDialog('csv', this.adminTeamsTable);
        });

        // departments tab
        this.departmentsDownloadCsvBtn.addEventListener('click', () => {
            this.adminDepartmentsTable.downloadDialog('csv', this.adminDepartmentsTable);
        });

        // roles tab
        this.rolesDownloadCsvBtn.addEventListener('click', () => {
            this.adminRolesTable.downloadDialog('csv', this.adminRolesTable);
        });

        this.addUserForm.addEventListener('hide.bs.offcanvas', async () => {
            await this.clearAddUserForm();
        });

    }

    async clearAddUserForm() {
        this.active.checked = false;
        setTomSelectById(this.department.id, []);
        this.email.value = '';
        this.firstName.value = '';
        this.fullName.value = '';
        this.lastName.value = '';
        this.manager.value = '';
        this.offCanvasTitle.innerHTML = 'Edit User'
        this.occupation.value = '';
        this.password.value = '';
        this.phone.value = '';
        setTomSelectById(this.team.id, '');
        setTomSelectById(this.role.id, [0]);
        this.userName.value = '';
    }

    async addUser() {
        const form = document.getElementById('form');
        const formData = new FormData(form);

        try {
            const response = await fetch('/api/people/add-user/', {
                method: 'POST',
                body: formData,  // send as form data, NOT JSON
            });

            const data = await response.json();

            if (response.ok && data.message) {
                await showSwal('Success', data.message, 'success');
                await this.clearAddUserForm();
                this.addUserOffcanvas.hide();
            } else {
                let errorText = 'An error occurred';
                if (data.details && Array.isArray(data.details)) {
                    errorText = data.details.join('\n');
                }
                await showSwal('Error', errorText, 'error');
            }
        } catch (error) {
            console.error('Submission error:', error);
            await showSwal('Error', `An error occurred during submission: ${error.message}`, 'error');
        }
    }


    setEventHandlers() {
        this.adminUsersTable.setRowDblClickEventHandler(async (e, row) => {
            await this.clearAddUserForm()
            const rowData = row.getData();
            this.userId.value = rowData.id;

            const response = await fetch(`/api/people/get-current-user/?id=${rowData.id}`)
            const data = await response.json()

            setTomSelectById(this.department.id, data['user_department_id']);
            setTomSelectById(this.team.id, data['user_team_id']);
            setTomSelectById(this.role.id, data['user_role_id']);
            setTomSelectById(this.manager.id, data['user_manager_id']);

            this.userAvatar.src = data['avatar'];

            this.occupation.value = data['user_occupation'];
            this.firstName.value = data['user_first_name'];
            this.lastName.value = data['user_last_name'];
            this.fullName.value = data['user_full_name'];
            this.userName.value = data['user_username'];
            this.email.value = data['user_email'];
            this.phone.value = data['user_phone'];
            this.email.value = data['user_email'];
            this.active.checked = data['user_active'];


            this.addUserOffcanvas.show();
        });
    }

    async csvImport() {
        // todo replace with a modal
        Swal.fire({
            title: 'Upload CSV',
            input: 'file',
            inputAttributes: {
                'accept': '.csv',
            },
            showCancelButton: true,
            confirmButtonColor: '#3085d6',
            cancelButtonColor: '#d33',
            confirmButtonText: 'Import!',
            cancelButtonText: 'Cancel',
            reverseButtons: true,
            showLoaderOnConfirm: true,
            preConfirm: (file) => {
                if (!file || file.type !== 'text/csv') {
                    Swal.showValidationMessage('Please upload a valid CSV file');
                    return false;
                }

                const formData = new FormData();
                formData.append('file', file);

                return fetch('/api/csv-user-import/', {
                    method: 'POST',
                    body: formData,
                })
                    .then((response) => {
                        if (!response.ok) {
                            return response.json().then((data) => {
                                Swal.showValidationMessage(`Request failed: ${data.error || data.message}`);
                            });
                        }
                        return response.json();
                    })
                    .catch((error) => {
                        Swal.showValidationMessage(`Request failed: ${error}`);
                    });
            },
            allowOutsideClick: () => !Swal.isLoading(),
        }).then(async (result) => {
            if (result.isConfirmed) {
                await showSwal('Success', result.value.message, 'success');

            }
        });
    }


    initializeInteractionMap() {
        this.interactionTabMap = {
            'user-admin-pane': {
                user: {
                    api: '/api/people/get-user-counts/',
                    div: 'all-users-status-count',
                    chart: 'bar',
                    title: 'Active vs Inactive Users',
                    xLabel: 'account_status',
                    scope: 'all',
                    type: 'users',
                    table: this.adminUsersTable
                },
                team: {
                    api: '/api/people/get-user-teams-counts/',
                    div: 'all-teams-count',
                    chart: 'bar',
                    title: 'Users per Team',
                    xLabel: 'Team',
                    scope: 'all',
                    type: 'users',
                    table: this.adminUsersTable
                },
                department: {
                    api: '/api/people/get-user-departments-counts/',
                    div: 'all-departments-count',
                    chart: 'bar',
                    title: 'Users per Department',
                    xLabel: 'Department',
                    scope: 'all',
                    type: 'users',
                    table: this.adminUsersTable
                }
            },
        };
    }

    async getUserColumns() {
        return [
            {
                title: 'Full Name',
                field: 'full_name',
            },
            {
                title: 'Phone',
                headerHozAlign: 'center',
                field: 'phone',
                hozAlign: 'center',
            },
            {
                title: 'Email',
                field: 'email',
            },
            {
                title: 'Department',
                headerHozAlign: 'center',
                field: 'department',
                hozAlign: 'center',
            },
            {
                title: 'Team',
                headerHozAlign: 'center',
                field: 'team',
                hozAlign: 'center',
            },
            {
                title: 'Occupation',
                field: 'occupation',
                headerHozAlign: 'center',
                hozAlign: 'center',
            },
            {
                title: 'Manager',
                field: 'manager',
                headerHozAlign: 'center',
                hozAlign: 'center',
            },
            {
                title: 'Active',
                field: 'active',
                hozAlign: 'center',
                formatter: 'tickCross',
            },
        ];
    }

    async getTeamColumns() {
        return [
            {
                title: 'ID',
                field: 'id',
                visible: false,
            },
            {
                title: 'Team Name',
                field: 'name',
                editor: 'input',
            },
            {
                title: 'Description',
                field: 'description',
                editor: 'input',
            },
            deleteColumn

        ]
    }

    async getDepartmentColumns() {
        return [
            {
                title: 'ID',
                field: 'id',
                visible: false,
            },
            {
                title: 'Department Name',
                field: 'name',
                editor: 'input',
            },
            {
                title: 'Description',
                field: 'description',
                editor: 'input',
            },
            deleteColumn
        ]
    }

    async getRoleColumns() {
        return [
            {
                title: 'ID',
                field: 'id',
                visible: false,
            },
            {
                title: 'Role',
                field: 'name',
            },
            {
                title: 'Description',
                field: 'description',
                editor: 'input',
            },
            deleteColumn
        ]
    }
}

const userDashboard = new UserDashboard();
await userDashboard.init()