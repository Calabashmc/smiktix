import {exists, showSwal} from '../../../../../static/js/includes/form-classes/form-utils.js';
import {outageClass} from './outage-class.js';
import {slaClass} from './sla-class.js';

class InteractionPriorityButtonsClass {
    constructor() {
        this.changeRiskCalc = document.getElementById('risk-calc');
        this.isMajor = document.getElementById('is-major');
        this.isMajorSpan = document.getElementById('is-major-span');
        this.outage = document.getElementById('outage');
        this.priority = document.getElementById('priority');
        this.priorityButtons = document.querySelectorAll('input[name="priority-matrix"]');
        this.priorityImpact = document.getElementById('priority-impact');
        this.priorityUrgency = document.getElementById('priority-urgency');
        this.slaPaused = document.getElementById('sla-paused');
        this.ticketNumber = document.getElementById('ticket-number');
        this.ticketType = document.getElementById('ticket-type');
    }

    async init() {
        this.setupListeners();
        await this.setPriorityButton();
    }

    setupListeners() {
        for (const btn of this.priorityButtons) {
            btn.addEventListener('click', async (event) => {
                if (!exists) {
                    event.preventDefault()
                    await showSwal('Ticket not saved yet', 'Please save your ticket before changing the priority', 'info')
                } else if (this.slaPaused.checked) {
                    event.preventDefault(); // don't set button to clicked
                    await showSwal('Paused', 'You cannot change the priority while paused', 'info');
                } else {
                    await this.updatePriorityValues(btn);
                    if(this.outage.checked) {
                        await outageClass.calculateOutageDuration();
                    }

                }
            });
        }
    }

    async setPriorityButton() {
        // Find the radio button matching current priority/urgency/impact
        const currentRadio = Array.from(this.priorityButtons).find(btn =>
            btn.dataset.priority === this.priority.value &&
            btn.dataset?.urgency === this.priorityUrgency.value.toLowerCase() &&
            btn.dataset?.impact === this.priorityImpact.value.toLowerCase()
        )

        if (currentRadio) {
            currentRadio.checked = true;
            await this.updatePriorityValues(currentRadio);
        }
    }

    async updatePriorityValues(button) {
        if (exists) {
            const {priority, urgency, impact} = button.dataset;
            this.priority.value = priority;
            this.priorityUrgency.value = urgency;
            this.priorityImpact.value = impact;

            await slaClass.setSlaDetails();
        }

        this.setPriorityColour();
        this.setUrgencyImpactColours();
    }

    setPriorityColour() {
        const priorityClasses = ['p-colour-p1', 'p-colour-p2', 'p-colour-p3', 'p-colour-p4', 'p-colour-p5'];
        this.priority.classList.remove(...priorityClasses);
        this.changeRiskCalc?.classList.remove(...priorityClasses);
        this.isMajorSpan?.classList.add('hide');

        const priorityClass = `p-colour-${this.priority.value.toLowerCase()}`;
        this.priority.classList.add(priorityClass);

        if (this.ticketType.value === 'Change') {
            this.changeRiskCalc.classList.add(`p-colour-${this.changeRiskCalc.value.toLowerCase()}`);
        }
    }

    setUrgencyImpactColours() {
        const levelToClass = {
            high: 'p-colour-p1',
            medium: 'p-colour-p3',
            low: 'p-colour-p5'
        };

        const updateElement = (element, value) => {
            element.classList.remove(...Object.values(levelToClass));
            element.classList.add(levelToClass[value]);
            element.value = value.charAt(0).toUpperCase() + value.slice(1); // capitalize
        };

        updateElement(this.priorityUrgency, this.priorityUrgency.value.toLowerCase());
        updateElement(this.priorityImpact, this.priorityImpact.value.toLowerCase());
    }
}

export const priorityButtonsClass = new InteractionPriorityButtonsClass();