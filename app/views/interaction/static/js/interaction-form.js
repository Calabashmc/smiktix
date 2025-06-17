import {tomSelectInstances} from '../../../../static/js/includes/tom-select.js';
import {formButtonHandlers} from '../../../../static/js/includes/form-classes/form-button-handlers.js';
import {priorityButtonsClass} from './includes/interaction-priority-button-class.js';
import {showSwal} from '../../../../static/js/includes/form-classes/form-utils.js';

class InteractionFormClass {
    constructor() {
        this.affectedCI = document.getElementById('affected-ci');
        this.categoryId = document.getElementById('category-id');
        this.form = document.getElementById('form')
        this.impact = document.getElementById('priority-impact');
        this.knowledgeResolveBtn = document.getElementById('knowledge-resolve-btn');
        this.priority = document.getElementById('priority');
        this.problemLinkSelect = document.getElementById('problem-id');
        this.problemLinkBtn = document.getElementById('problem-id-btn');
        this.rapidResolveBtn = document.getElementById('rapid-resolve-btn');
        this.requestedBy = document.getElementById('requested-by');
        this.resolutionCodeId = document.getElementById('resolution-code-id');
        this.resolutionSelect = document.getElementById('rapid-resolve');
        this.shortDescription = document.getElementById('short-desc');
        this.status = document.getElementById('status');
        this.subCategory_id = document.getElementById('subcategory-id');

        this.supportTeam = document.getElementById('support-team');
        this.ticketNumber = document.getElementById('ticket-number');
        this.ticketType = document.getElementById('ticket-type');
        this.urgency = document.getElementById('priority-urgency');
    }

    init() {
        this.setupListeners();
    }

    setupListeners() {
        this.affectedCI.addEventListener('change', async () => {
            await this.setPriorityOnCiImportance();
        });

        this.knowledgeResolveBtn.addEventListener('click', async () => {
            await showSwal("not yet implemented", "coming soon", "info");
        })

        this.problemLinkBtn.addEventListener('click', () => {
            this.handleProblemLink();
        })

        this.rapidResolveBtn.addEventListener('click', async (e) => {
            await this.handleRapidResolve(e)
        });

    }



    async setPriorityOnCiImportance() {
        const ciId = this.affectedCI.options[this.affectedCI.selectedIndex].value;

        const response = await fetch('/api/interaction/get-ci-importance/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({'ci_id': ciId})
        });

        const data = await response.json();
        if (response.ok) {
            this.priority.value = data['priority'];
            this.impact.value = data['impact'];
            this.urgency.value = data['urgency'];
            await priorityButtonsClass.setPriorityButton()
        } else {
            await showSwal('Error', data['error'], 'error');
        }


    }

    handleProblemLink() {
        const selectedOption = this.problemLinkSelect.options[this.problemLinkSelect.selectedIndex].text;
        const ticketNumber = selectedOption.split(' | ')[0];
        if (!ticketNumber) {
            return;
        }
        const url = `/ui/problem/ticket/?ticket=${ticketNumber}`; // Modify this URL structure as needed
        window.open(url, '_blank');
    }

    async handleRapidResolve(e) {
        if (!this.requestedBy.value) {
            await showSwal('Requester not selected', 'Select a requester before proceeding with rapid resolution', 'warning');

            this.requestedBy.tomselect.focus();  // focuses the TomSelect input
            return
        }
        const tomSelectInstance = tomSelectInstances.get(this.resolutionSelect.id);
        const resolution_id = tomSelectInstance ? tomSelectInstance.getValue() : '';

        if (resolution_id === '') {
            await showSwal('Resolution not selected', 'Select a rapid resolution template', 'warning');

        } else {
            const response = await showSwal(
                'Are you sure?',
                'Existing form content will be replaced and status set to Resolved. This cannot be undone.',
                'question'
            );

            if (response.isConfirmed) {
                const apiArgs = {
                    'resolution-id': resolution_id,
                }

                const response = await fetch('/api/interaction/set-rapid-resolution/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(apiArgs)
                });

                const data = await response.json();
                const category_id = data['category_id'];

                if (response.ok && data) {
                    console.log(data)
                    this.shortDescription.value = data['short_description'];
                    this.categoryId.tomselect.setValue(category_id);
                    // wait for category_id to populate

                    this.priority.value = data['priority'];
                    this.impact.value = data['priority_impact'];
                    this.urgency.value = data['priority_urgency']
                    this.supportTeam.tomselect.setValue(data['support_team_id']);
                    this.resolutionCodeId.value = data['resolution_code_id'];
                    this.status.value = 'Resolved';
                    this.ticketType.value = 'Incident';
                    setTimeout(() => {
                        this.subCategory_id.tomselect.setValue(data['subcategory_id']);
                    }, 100);
                }
                setTimeout(async () => {
                    await formButtonHandlers.handleSubmitBtn(e)
                }, 100);
            }
        }
    }
}

export const interactionFormClass = new InteractionFormClass()