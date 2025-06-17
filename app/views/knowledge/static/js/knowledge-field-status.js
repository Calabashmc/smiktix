import {fieldStatusClass} from '../../../../static/js/includes/form-classes/fieldstatus-class.js';


class KnowledgeFieldStatus {
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
            case 'internal':
                await fieldStatusClass.disableAfterNew();
                break;
            case 'archived':
                await fieldStatusClass.setIfClosed();
                break;

        }
    }
}

export const knowledgeStatus = new KnowledgeFieldStatus();