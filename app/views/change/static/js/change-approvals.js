import {tomSelectInstances} from '../../../../static/js/includes/tom-select.js';
import {showSwal} from '../../../../static/js/includes/form-classes/form-utils.js';
// todo make this an approvals class and split out the success/fail reasons into a changeResolutionsClass
class ChangeApprovalsClass {
    constructor() {
        this.approvalStakeholders = document.getElementById('approval-stakeholders');
        this.addAproverBtn = document.getElementById('add-approver-btn');
        this.approversSelection = document.getElementById('approvers-selection');
        this.cabReady = document.getElementById('cab-ready');
        this.countApproved = document.getElementById('approved-count');
        this.countDenied = document.getElementById('denied-count');
        this.countPending = document.getElementById('pending-count');

        this.notifyApproversBtn = document.getElementById('notify-approvers-btn');
        this.removeApproverBtn = document.getElementById('remove-approver-btn')
        this.ticketNumber = document.getElementById('ticket-number');
        this.ticketType = document.getElementById('ticket-type');
    }

    init() {
        this.setupListeners();
        this.updateCount();
    }

    setupListeners() {
        this.addAproverBtn?.addEventListener('click', async () => {
            await this.addApprover()
        })

        this.removeApproverBtn.addEventListener('click', async () => {
            await this.removeApprover()
        })

        this.notifyApproversBtn.addEventListener('click', async () => {
            await this.renotifyApprovers()
        })

        this.cabReady.addEventListener('change', async (e) => {
            if (e.target.checked) {
                const response = await showSwal(
                    'Are you sure?',
                    '<p>Are all Plans in place?</p>' +
                    '<p>Have Approvers responded?</p>' +
                    '<p>Is the Release ready?</p><br>' +
                    '<p>If yes then this will be brought before the next CAB.</p>',
                    'question'
                )

                if (!response.isConfirmed) {
                    e.target.checked = false;
                } else {
                    // Programmatically Click on the CAB step if read for CAB is checked
                    const button = document.querySelector('.step-button.enabled[data-step-id="cab"]');
                    if (button) {
                        button.dispatchEvent(new Event('click', {bubbles: true}));
                    }
                }
            }
        })
    }

    async addApprover() {
        const sourceSelectId = this.approvalStakeholders.id;
        const sourceSelect = tomSelectInstances.get(sourceSelectId);
        const selectedValue = sourceSelect.getValue(); // Get the selected value directly from TomSelect
        const selectedText = sourceSelect.getOption(selectedValue)?.textContent; // Get the selected text directly from TomSelect

        if (selectedValue === '0') {
            await showSwal('Error', 'Please select an approver', 'error');
        } else {
            // Clear the selected option from the TomSelect
            sourceSelect.clear();
            sourceSelect.removeOption(selectedValue);
            sourceSelect.refreshItems();

            // Create and append the new option to the approvers selection
            const newOption = new Option(selectedText + ' : Pending Approval', selectedValue);
            this.approversSelection.appendChild(newOption);
            newOption.selected = true;

            // Update the count
            this.updateCount();

            const apiArgs = {
                'approver': selectedValue,
                'ticket-number': this.ticketNumber.value,
            };

            try {
                const response = await fetch('/api/change/add-approver/', {
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

            } catch (error) {
                console.error('Error adding approver:', error);
            }
        }
    }

    async removeApprover() {
        const sourceSelect = this.approversSelection;
        const selected = sourceSelect.options[sourceSelect.selectedIndex];
        const destinationTom = tomSelectInstances.get(this.approvalStakeholders.id);


        if (!selected.value) {
            await showSwal('Error', 'Please select an approver', 'error');
            return
        }
        if (selected.value) {
            // Find the option element by its value
            const optionToRemove = Array.from(sourceSelect.options).find(option => option.value === selected.value);
            // Remove the option if it exists
            if (optionToRemove) {
                if (optionToRemove instanceof HTMLOptionElement) {
                    sourceSelect.removeChild(optionToRemove);
                }
            }

            const splitValue = selected.textContent.split(':')[0].trim();
            // Create and append the new option to the stakeholders selection
            destinationTom.addOption({
                value: selected.value,
                text: splitValue
            })

            destinationTom.refreshItems();

            this.updateCount();

            const apiArgs = {
                'approver': selected.value,
                'ticket-number': this.ticketNumber.value,
            };

            try {
                const response = await fetch('/api/change/remove-approver/', {
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

            } catch (error) {
                console.error('Error removing approver:', error);
            }
            // return selected.text
        }
    }



    async renotifyApprovers() {
        const response = await showSwal(
            'Are you sure?',
            'Stakeholders are notified when added to the Approvers list.<br>' +
            '<br>Continuing will re-send notifications to all selected approvers.',
            'question'
        );

        if (!response.isConfirmed) return;

        const selectedApprovers = Array.from(this.approversSelection.options)
            .filter(option => option.selected)
            .map(option => option.value);

        if (selectedApprovers.length === 0) {
            await showSwal('Error', 'Please select one or more approvers to notify.', 'error');
            return;
        }

        const apiRequests = selectedApprovers.map(approver => {
            const apiArgs = {
                'approver': approver,
                'ticket-number': this.ticketNumber.value,
            };

            return fetch('/api/change/add-approver/', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(apiArgs),
            })
                .then(response => response.json().then(data => ({response, data})));
        });

        try {
            const results = await Promise.all(apiRequests);

            const errors = results.filter(({response}) => !response.ok);
            const successes = results.filter(({response}) => response.ok);

            if (errors.length > 0) {
                const errorMessages = errors.map(({data}) => data.error).join('<br>');
                await showSwal('Error', errorMessages, 'error');
            }

            if (successes.length > 0) {
                const successMessages = successes.map(({data}) => data.message).join('<br>');
                await showSwal('Success', successMessages, 'success');
            }
        } catch (error) {
            await showSwal('Error', error.message, 'error');
        }
    }


    updateCount() {
        const options = this.approversSelection.options;
        let approvedCount = 0;
        let deniedCount = 0;
        let pendingCount = 0;

        for (let i = 0; i < options.length; i++) {
            const optionText = options[i].textContent.toLowerCase();
            if (optionText.includes('approved')) {
                approvedCount++;
            }
            if (optionText.includes('denied')) {
                deniedCount++;
            }
            if (optionText.includes('pending')) {
                pendingCount++;
            }
        }
        this.countApproved.textContent = approvedCount.toString();
        this.countDenied.textContent = deniedCount.toString();
        this.countPending.textContent = pendingCount.toString();
    }

}

export const changeApprovalsClass = new ChangeApprovalsClass()