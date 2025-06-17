    import {fieldStatusClass} from '../../../../../static/js/includes/form-classes/fieldstatus-class.js';
    import {showSwal} from '../../../../../static/js/includes/form-classes/form-utils.js';

    export class InteractionFieldStatusClass {
        constructor() {
            this.status = document.getElementById('status');
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
                case 'in-progress':
                    await showSwal('SLA Response time saved', '', 'success', true, 'top-end');
                    await fieldStatusClass.setIfInProgress();
                    break;
                case 'resolved':
                    await fieldStatusClass.setIfResolved();
                    break;
                case 'review':
                    console.log('in review');
                    await fieldStatusClass.setIfReview()
                    break;
                case 'closed':
                    await fieldStatusClass.setIfClosed();
                    break;
                default:
                    console.warn(`Unhandled status: ${status}`);
            }
        }
    }