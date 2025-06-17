import {exists, saveNotes, showSwal} from '../../../../../static/js/includes/form-classes/form-utils.js';

class ChangeRiskButtonsClass {
    constructor() {
        this.risk = document.getElementById('priority');
        this.riskCalc = document.getElementById('risk-calc');
        this.changeRiskBtns = document.querySelectorAll('input[name="priority-matrix"]');
        this.ticketNumber = document.getElementById('ticket-number');

        this.riskColourMap = {
            'CR1': 'p-colour-p1',
            'CR2': 'p-colour-p2',
            'CR3': 'p-colour-p3',
            'CR4': 'p-colour-p4',
            'CR5': 'p-colour-p5'
        };

        this.riskClasses = Object.values(this.riskColourMap).map(String);


    }

    init() {
        this.setupListeners();
        this.setBtnToRisk();

        // Set initial colours for both elements independently
        this.updateRiskColour(this.risk);
        if (this.riskCalc) {
            this.updateRiskColour(this.riskCalc);
        }
    }

    setupListeners() {
        for (const btn of this.changeRiskBtns) {
            btn.addEventListener('click', async (event) => {
                if (!exists) {
                    event.preventDefault();
                    await showSwal('Ticket not saved yet', 'Please save your ticket before changing the priority', 'info');
                } else {
                    this.risk.value = btn.value;
                    this.updateRiskColour(this.risk);
                    await this.saveRisk();
                }
            });
        }

        // Add listeners to update calculated risk colour on input change for each independently
        this.riskCalc?.addEventListener('change', () => {
            this.updateRiskColour(this.riskCalc);
        });
    }

    setRiskColour(risk) {
        // This method is now mainly unused but kept for backward compatibility,
        // Prefer updateRiskColour(element) which is more flexible
        const newClass = this.riskColourMap[risk];
        if (!newClass) return;

        this.risk.classList.remove(...this.riskClasses);
        this.risk.classList.add(newClass);
        return newClass;
    }

    setBtnToRisk() {
        for (const btn of this.changeRiskBtns) {
            btn.checked = (btn.value === this.risk.value);
        }
        const colourClass = this.setRiskColour(this.risk.value);
    }

    async saveRisk() {
        const currentPriority = this.risk.value;
        const apiArgs = {
            'risk': this.risk.value,
            'ticket-number': this.ticketNumber.value,
        };

        const response = await fetch('/api/change/set-change-risk/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(apiArgs),
        });

        const data = await response.json();

        if (response.ok) {
            await saveNotes(`Risk changed to: ${this.risk.value}`, true);
        } else {
            await showSwal('Error', data['error'], 'error');
            this.risk.value = currentPriority;  // revert priority on error
            this.updateRiskColour(this.risk);
        }
    }

    updateRiskColour(element) {
        element.classList.remove(...this.riskClasses);
        const val = element.value;
        const cls = this.riskColourMap[val];
        if (cls) {
            element.classList.add(cls);
        }
    }
}

export const changeRiskButtonsClass = new ChangeRiskButtonsClass();
