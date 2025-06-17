import {priorityButtonsClass} from './interaction-priority-button-class.js';
import {
    exists, hideFormButtons,
    saveNotes,
    showSwal
} from '../../../../../static/js/includes/form-classes/form-utils.js';

class OutageClass {
    constructor() {
        this.impact = document.getElementById('priority-impact');
        this.isMajor = document.getElementById('is-major');
        this.isMajorSpan = document.getElementById('is-major-span');
        this.outage = document.getElementById('outage');
        this.outageDurationSla = document.getElementById('outage-duration-sla');
        this.outageDurationTotal = document.getElementById('outage-duration-total');
        this.outageEnd = document.getElementById('outage-end');
        this.outageStart = document.getElementById('outage-start');
        this.p1Btn = document.getElementById('high-high');
        this.priority = document.getElementById('priority');
        this.ticketNumber = document.getElementById('ticket-number');
        this.urgency = document.getElementById('priority-urgency');
        this.form = document.getElementById('form');
    }

    init() {
        this.checkOutageState();
        this.setupListeners();
    }

    checkOutageState() {
        if (this.outage.checked) {
            if (!this.outageStart.value || !this.outageEnd.value) {
                this.outageStart.value = '';
                this.outageEnd.value = '';
                this.outage.checked = false;
                this.outageStart.classList.remove('is-invalid');
                this.outageEnd.classList.remove('is-invalid');
                this.outageStart.disabled = true;
                this.outageEnd.disabled = true;

            } else {
                this.outageStart.disabled = false;
                this.outageEnd.disabled = false;
            }
        } else {
            this.outageStart.classList.remove('is-invalid');
            this.outageEnd.classList.remove('is-invalid');
            this.outageStart.value = '';
            this.outageEnd.value = '';
            this.outageStart.disabled = true;
            this.outageEnd.disabled = true;
        }
    }

    setupListeners() {
        this.outage.addEventListener('click', async () => {
            if (exists) {
                await this.handleOutageClick();
            } else {
                await showSwal('Ticket not saved yet', 'Please save your ticket before setting an outage', 'info');
                this.outage.checked = false;
            }
        })

        this.outageStart.addEventListener('change', () => {
            this.handleStartChange();
        });

        this.outageEnd.addEventListener('change', async () => {
            await this.handleEndChange();
        });
    }

    handleStartChange() {
        this.outageEnd.disabled = false;
        this.outageEnd.value = '';
    }

    async handleEndChange() {
        const startDateTime = new Date(this.outageStart.value);
        const endDateTime = new Date(this.outageEnd.value);

        if (endDateTime < startDateTime) {
            await showSwal('End time must be after start time', 'Start time must be before end time', 'error');
            this.outageEnd.value = '';
            this.outageStart.value = '';
        } else {
            this.calculateOutageDuration().then(async () => {
                const totalHours = this.outageDurationTotal.value;
                const slaHours = this.outageDurationSla.value;
                await saveNotes(`Outage set to: Total: ${totalHours} Business Hours: ${slaHours}`, true);
                await this.saveRecord();
            });
        }
    }

    async handleOutageClick() {
        if (this.outage.checked) {
            this.priority.value = 'P1';
            this.urgency.value = 'High';
            this.impact.value = 'High';
            this.p1Btn.checked = true;
            this.isMajorSpan.classList.remove('hide');
            this.isMajor.checked = true;
            this.outageStart.disabled = false;
            this.outageStart.required = true;
            this.outageEnd.required = true;
        } else {
            const response = await showSwal('Clear Outage', 'Are you sure you want to clear the outage?', 'question');
            if (response.isConfirmed) {
                await this.clearOutage();
            } else {
                this.outage.checked = true;
            }

        }
    }

    async clearOutage() {
        const response = await fetch('/api/lookup/get-app-defaults/');
        const data = await response.json();
        console.log(data['incident_default_priority'])
        if (!response.ok) {
            await showSwal('Error', data['error'], 'error');
        }

        this.outageDurationTotal.value = '00:00';
        this.outageDurationSla.value = '00:00';
        this.isMajor.checked = false;

        this.priority.value = data['incident_default_priority'];
        this.urgency.value = data['incident_default_urgency'].toLowerCase();
        this.impact.value = data['incident_default_impact'].toLowerCase();

        this.isMajorSpan.classList.add('hide');
        await priorityButtonsClass.setPriorityButton();

        this.outageStart.classList.remove('is-invalid');
        this.outageStart.required = false;
        this.outageStart.value = '';
        this.outageStart.readOnly = true;

        this.outageEnd.classList.remove('is-invalid');
        this.outageEnd.required = false;
        this.outageEnd.value = '';
        this.outageEnd.readOnly = true;

        this.outage.checked = false;

        await saveNotes('Outage cleared and reset to 00:00');
        await this.saveRecord();
    }

    async calculateOutageDuration() {
        const apiArgs = {
            outage_start: this.outageStart.value,
            outage_end: this.outageEnd.value,
            priority: this.priority.value,
        };

        const response = await fetch(`/api/interaction/outage-calc/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(apiArgs),
        })
        const data = await response.json();

        if (!response.ok) {
            await showSwal('Error', data['error'], 'error');
        } else {
            console.log(data)
            this.outageDurationTotal.value = data['total_time'];
            this.outageDurationSla.value = data['sla_time'];
        }
    }

    async saveRecord() {
        const apiArgs = {
            impact: this.impact.value,
            is_major: this.isMajor.checked,
            outage: this.outage.checked,
            outage_start: this.outageStart.value,
            outage_end: this.outageEnd.value,
            outage_duration_total: this.outageDurationTotal.value,
            outage_duration_sla: this.outageDurationSla.value,
            priority: this.priority.value,
            ticket_number: this.ticketNumber.value,
            urgency: this.urgency.value,
        };

        const response = await fetch('/api/interaction/set-interaction-ticket/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(apiArgs),
        });

        const data = await response.json();

        if (!response.ok) {
            await showSwal('Error', data['error'], 'error');
        } else {
            this.outageStart.classList.remove('is-invalid');
            this.outageEnd.classList.remove('is-invalid');
            hideFormButtons()
            await priorityButtonsClass.setPriorityButton();
        }
    }
}

export const outageClass = new OutageClass();