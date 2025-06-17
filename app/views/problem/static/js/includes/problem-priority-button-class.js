import {exists, saveNotes, showSwal} from '../../../../../static/js/includes/form-classes/form-utils.js';

class ProblemPriorityButtonClass {
    constructor() {
        this.priority = document.getElementById('priority');
        this.priorityBtns = document.querySelectorAll('input[name="priority-matrix"]');
        this.ticketNumber = document.getElementById('ticket-number');

        this.currentPriority = this.priority.value;
    }

    init() {
        this.setupListeners();
        this.setBtnToPriority()
    }

    setupListeners() {
        for (const btn of this.priorityBtns) {
            btn.addEventListener('click', async (event) => {
                if (!exists) {
                    event.preventDefault()
                    await showSwal('Ticket not saved yet', 'Please save your ticket before changing the priority', 'info')
                } else {
                    this.priority.value = btn.value;
                    this.setPriorityColour()
                    await this.savePriority()
                }
            })
        }
    }

    setBtnToPriority() {
        for (const btn of this.priorityBtns) {
            if (btn.value === this.priority.value) {
                btn.checked = true;
                this.setPriorityColour()
            }
        }
    }

    async savePriority() {
        const apiArgs = {
            'priority': this.priority.value,
            'ticket_number': this.ticketNumber.value,
        }

        const response = await fetch('/api/problem/set-problem-priority/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(apiArgs)
        })

        const data = await response.json();

        if (response.ok) {
            await saveNotes(`Priority changed to: ${this.priority.value}`, true);
        } else {
            await showSwal('Error', data['error'], 'error');
            this.priority.value = this.currentPriority;  // revert priority if error
        }
    }

    setPriorityColour() {
        const priorityClasses = ['p-colour-p1', 'p-colour-p2', 'p-colour-p3', 'p-colour-p4', 'p-colour-p5'];
        this.priority.classList.remove(...priorityClasses);

        const priorityClass = `p-colour-${this.priority.value.toLowerCase()}`;
        this.priority.classList.add(priorityClass);
    }
}

export const priorityButtonsClass = new ProblemPriorityButtonClass();