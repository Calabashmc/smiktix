import {showSwal} from '../../../../static/js/includes/form-classes/form-utils.js';


export class ChangeCabClass {
    constructor() {
        this.cabApprovalStatus = document.getElementById('cab-approval-status');
        this.cabAppovalStatusBtns = document.querySelectorAll('input[type="radio"][name="cab-approval-status"]');
        this.changeCancelled = document.getElementById('change-cancelled');
        this.form = document.getElementById('form');
        this.requirementChecks = document.querySelectorAll('input[type="checkbox"][id^="cab_check_"]');
        this.status = document.getElementById('status')
        this.ticketNumber = document.getElementById('ticket-number');
    }

    init() {
        this.setupListeners();
        this.setBtnValue();
    }

    disableCabApprovalStatusBtns() {
        this.cabAppovalStatusBtns.forEach(btn => {
            btn.disabled = true;
        });
    }

    setupListeners() {

        this.cabAppovalStatusBtns.forEach(btn => {
            btn.addEventListener('click', async () => {
                this.cabApprovalStatus.value = btn.value;
                this.changeCancelled.checked = btn.value === 'denied';

                if (btn.value === 'approved') {
                    const result = await this.checkChangeRequirements();
                    if (!result) {
                        const response = await showSwal(
                            'Check Requirements',
                            'Not all Change Requirements are checked. Proceed with Approval?',
                            'question'
                        );

                        if (!response.isConfirmed) {
                            this.cabAppovalStatusBtns.forEach(btn => {
                                if (btn.value === 'pending') {
                                    btn.checked = true;
                                    this.cabApprovalStatus.value = btn.value;
                                }
                            })
                        }else{
                            await this.saveCabApprovalStatus();
                        }
                    } else {
                        await this.saveCabApprovalStatus();
                    }
                    // Programmatically Click on the Implement
                    const button = document.querySelector('.step-button.enabled[data-step-id="implement"]');
                    if (button) {
                        button.dispatchEvent(new Event('click', {bubbles: true}));
                    }
                }

                if (btn.value === 'denied') {
                    this.changeCancelled.checked = true;
                    await this.saveCabApprovalStatus();
                    // Programmatically Click on the Review step
                    const button = document.querySelector('.step-button.enabled[data-step-id="review"]');
                    if (button) {
                        button.dispatchEvent(new Event('click', {bubbles: true}));
                    }
                }
            })
        })
    }

    setBtnValue() {
        // Set the button value from the record - disables buttons if already approved/denied
        this.cabAppovalStatusBtns.forEach(btn => {
            if (btn.value === this.cabApprovalStatus.value) {
                btn.checked = true;
                if (btn.value !== 'pending') {
                    this.disableCabApprovalStatusBtns();
                }
            }
        })
    }

    async saveCabApprovalStatus() {
         let cabCheckData = {};
         // get the id and check the state of the checkboxes

        for (const checkbox of this.requirementChecks) {
             cabCheckData[checkbox.id] = checkbox.checked;
         }

        const apiArgs = {
            'ticket-number': this.ticketNumber.value,
            'cab-approval': this.cabApprovalStatus.value,
            'checkbox-data': cabCheckData
        }
        const response = await fetch('/api/change/set-cab-outcome/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(apiArgs)
        });
        const data = await response.json();

        if (!response.ok) {
            await showSwal('Error', data['error'], 'error');
        }
    }

    async checkChangeRequirements() {
        for (const check of this.requirementChecks) {
            console.log(check.checked)
            if (!check.checked) {
                return false;
            }
        }
        return true;
    }

}

