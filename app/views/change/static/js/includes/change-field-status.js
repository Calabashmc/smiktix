import {fieldStatusClass} from '../../../../../static/js/includes/form-classes/fieldstatus-class.js';

export class ChangeFieldStatusClass {
    constructor() {
        this.addApproverBtn = document.getElementById('add-approver-btn');
        this.cabReady = document.getElementById('cab-ready');
        this.removeApproverBtn = document.getElementById('remove-approver-btn');
        this.status = document.getElementById('status');
        this.submitBtn = document.getElementById('submit-btn');
    }

    async init() {
        this.setupListeners();
        await this.setFieldsBasedOnStatus();
    }

    setupListeners() {
        this.status.addEventListener('change', async () => {
            await this.setFieldsBasedOnStatus();
        });
    }

    async setFieldsBasedOnStatus() {
        const status = this.status?.value.toLowerCase();

        switch (status) {
            case 'plan':
                await fieldStatusClass.disableAfterNew();
                break;
            case 'build':
                await fieldStatusClass.disableAfterNew();
                break;
            case 'approval':
                await fieldStatusClass.disableAfterNew();
                break;
            case 'cab':
                await fieldStatusClass.disableAfterNew();
                await this.disableForCab();
                break;
            case 'implement':
                await fieldStatusClass.disableAfterNew();
                if (this.cabReady) {
                    await this.disableForCab();
                }
                await this.disableForImplement();
                break;
            case 'resolved':
                await fieldStatusClass.setIfResolved();
                break;
            case 'review':
                await fieldStatusClass.setIfClosed();
                this.submitBtn.disabled = false;
                break;
            case 'closed':
                await fieldStatusClass.setIfClosed();
                break;
            default:
                console.warn(`Unhandled status: ${status}`);
        }
    }

    async disableForCab() {
        this.cabReady.disabled = true;
        this.addApproverBtn.disabled = true;
        this.removeApproverBtn.disabled = true;
    }

    async disableForImplement() {
        const cabTabPane = document.getElementById('cab-tab-pane');
        if (cabTabPane) {
            const inputs = activeTabPane.querySelectorAll('input, select, textarea'); // Get all form elements
            inputs.forEach(input => {
                input.disabled = true; // Disable each input element
            });
        }
    }
}