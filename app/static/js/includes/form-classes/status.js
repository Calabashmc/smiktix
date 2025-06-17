import {StatusStepper} from './stepper.js';
import {saveNotes} from './form-utils.js';
import {exists, showSwal} from './form-utils.js';


export class StatusClass {
    constructor(steps) {
        // these are not on all forms so filter out when not present
        this.approved = this.getById('approved', false);
        this.cabReady = this.getById('cab-ready', false);
        this.releaseSuccessful = this.getById('release-successful', false);
        this.testSuccessful = this.getById('test-successful', false);

        // these are always present
        this.status = this.getById('status');
        this.stepper = this.getById('stepper-stage');
        this.tabs = [];
        this.ticketNumber = this.getById('ticket-number', false);
        this.ticketType = this.getById('ticket-type');

        this.steps = steps
        this.status = this.getById('status');
        this.statusStepper = new StatusStepper('stepper-stage', this.steps);
    }

    getById(id, required = true) {
        const element = document.getElementById(id);
        if (!element && required) {
            throw new Error(`Element with ID '${id}' not found`);
        }
        return element;
    }


    init() {
        this.setupListeners();
        this.statusStepper.setCurrentStep(this.status.value.toLowerCase());
        this.tabsToStatus();
    }

    setupListeners() {
        this.stepper.addEventListener('stepchange', async ({detail}) => {
            if (this.stepper.closest('.offcanvas')) return;
            this.tabs = detail.tabs;
            await this.stepAction(detail);
        });

        document.addEventListener('resolutionModalClosed', () => {
            if (this.status.value !== 'resolved') {
                this.statusStepper.setCurrentStep('in-progress');
            }
        });

        document.addEventListener('resolutionAdded', async () => {
            await this.updateStatus('resolved');
        });
    }

    async stepAction({step, title, message, tabs}) {
        const updateIf = async (condition, nextStep = step) => {
            if (condition) {
                await this.updateStatus(nextStep);
            } else {
                await this.goToPriorStep(title, message);
            }
        };

        switch (step) {
            case 'in-progress':
                if (!exists) {
                    await updateIf(false);
                } else if (this.status.value === 'new') {
                    await updateIf(true);

                } else if (this.status.value === 'resolved') {
                    const response = await showSwal('Ticket Resolved', 'Revert back to In Progress?', 'question', true);
                    if (response.isConfirmed) {
                        await updateIf(true);
                    } else {
                        this.status.value = 'resolved';
                        this.statusStepper.setCurrentStep('resolved');
                        this.status.dispatchEvent(new Event('change'));
                    }
                }
                break;

            case 'configuring':
            case 'ideation':
            case 'internal':
            case 'plan':
            case 'build':
                await updateIf(exists);
                break;

            case 'approval':
                await updateIf(this.testSuccessful?.checked);
                break;

            case 'cab':
                await updateIf(this.cabReady?.checked);
                break;

            case 'implement': {
                const eCabApproved = this.getById('ecab-approved', false);
                const changeType = this.getById('change-type');
                await updateIf(!(changeType.value === 'Emergency' && !eCabApproved?.checked));
                break;
            }

            case 'published': {
                const confirmed = (await showSwal(title, message, 'question')).isConfirmed;
                if (confirmed) {
                    await this.updateStatus(step);
                } else {
                    const fallbackStep = this.status.value === 'reviewing' ? 'reviewing' : 'internal';
                    this.statusStepper.setCurrentStep(fallbackStep);
                    this.tabsToStatus();
                }
                break;
            }

            case 'release':
                await updateIf(this.approved?.checked);
                break;

            case 'deploy':
                await updateIf(this.releaseSuccessful?.checked);
                break;

            case 'resolved':
                if (this.status.value !== 'resolved') {
                    document.dispatchEvent(new CustomEvent('statusStepChange', {detail: {step}}));
                }
                break;

            case 'closed': {
                if (this.status.value !== 'closed') {
                    const confirmed = (await showSwal(title, message, 'question')).isConfirmed;
                    if (confirmed) {
                        await this.updateStatus(step);
                    } else {
                        let priorStep = this.statusStepper.getPreviousStep();
                        this.statusStepper.setCurrentStep(priorStep);
                    }
                } else {
                    await showSwal('Ticket Closed', 'Ticket has already been closed', 'info');
                }
                break;
            }

            default:
                await this.updateStatus(step);
                break;
        }

        if (exists) this.tabsToStatus(tabs);
    }

    async goToPriorStep(title = null, message = null) {
        let priorStep = this.statusStepper.getPreviousStep();
        if (this.status.value === 'resolved') {
            priorStep = 'in-progress'
        }

        if (title || message) await showSwal(title, message, 'warning');

        this.statusStepper.setCurrentStep(priorStep);

        if (exists) {
            await this.updateStatus(priorStep);
            this.tabsToStatus();
        }
    }

    tabsToStatus() {
        // Collect all possible tab IDs from all steps
        const allTabs = new Set();
        for (const step of this.steps) {
            step.tabs.forEach(tab => allTabs.add(tab));
        }

        // Disable all tabs first
        for (const tab of allTabs) {
            const el = this.getById(tab);
            if (el) el.classList.add('disabled');
        }

        // Enable only the tabs for the current status
        const currentStep = this.steps.find(step => step.id === this.status.value.toLowerCase());
        if (currentStep) {
            this.enableTab(currentStep.tabs);
        }

        this.detailsTab = this.getById('details-tab', false) || this.getById('change-details-tab', false);
        if (this.detailsTab) {
            this.detailsTab.click();
        }
    }

    enableTab(tabs) {
        for (const tab of tabs) {
            this.getById(tab).classList.toggle('disabled', false);
        }
    }

    async updateStatus(statusText) {
        let apiArgs = {
            'ticket_number': this.ticketNumber.value,
            'ticket-type': this.ticketType.value,
            'status': statusText,
        };

        const response = await fetch(`/api/update-status/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(apiArgs)
        })

        if (response.ok) {
            let worklog = `Ticket status has changed to ${statusText}`
            await saveNotes(worklog, true);

            this.status.value = statusText
            this.status.dispatchEvent(new Event('change')); // hidden field so needs to trigger manually
        }

    }
}
