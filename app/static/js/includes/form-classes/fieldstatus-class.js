import { sunEditorClass } from '../suneditor-class.js';
import { tomSelectInstances } from '../tom-select.js';

class FieldStatusClass {
    constructor() {
        this.editResolutionBtn = this.getById('btn-edit-resolution', false);
        this.emailLink = this.getById('email');
        this.parentIdBtn = this.getById('parent-id-btn', false);
        this.phoneLink = this.getById('phone');
        this.rapidResolveBtn = this.getById('rapid-resolve', false);
        this.requestedBy = this.getById('requested-by', false) || this.getById('author-id', false) || this.getById('owner-id', false);
        this.requestedByBtn = this.getById('requested-by-btn', false) || this.getById('author-id-btn', false) || this.getById('owner-id-btn', false);
        this.resolutionAddBtn = this.getById('modal-add-resolution-btn');
        this.resolutionCancelBtn = this.getById('modal-cancel-resolution');
        this.resolutionCode = this.getById('resolution-code-id');
        this.source = this.getById('source-id', false);
        this.submitBtn = this.getById('submit-btn');
        this.status = this.getById('status');
        this.ticketform = this.getById('form');
    }

    getById(id, required = true) {
        const element = document.getElementById(id);
        if (!element && required) {
            throw new Error(`Element with ID '${id}' not found`);
        }
        return element;
    }

    async disableAfterNew() {
        this.requestedByTomSelectInstance = await tomSelectInstances.get(this.requestedBy.id);
        if (this.requestedByTomSelectInstance) {
            this.requestedByTomSelectInstance.disable();
        }
        if (this.rapidResolveBtn) {
            this.rapidResolveBtn.disabled = true;
        }
        this.requestedByBtn.disabled = true;
    }

    async setIfInProgress() {
        await this.disableAfterNew();
        this.enableFields([
            'short-desc',
            'source',
            'category',
            'subcategory',
            'support-team',
            'support-agent',
            'affected-ci',
            'problem-id',
            'outage',
            'knowledge-resolve-btn',
            'rapid-resolve-btn'
        ]);
        sunEditorClass.enableSingleEditor('details');
        sunEditorClass.enableSingleEditor('worklog');
    }

    async setIfResolved() {
        await this.disableAfterNew();
        this.setIfClosed();
        this.enableButtons([
            this.resolutionAddBtn,
            this.resolutionCancelBtn,
            this.editResolutionBtn,
            this.resolutionCode
        ]);
        sunEditorClass.enableSingleEditor('review-notes');
        sunEditorClass.enableSingleEditor('resolution-notes');
    }

    async setIfReview() {
        await this.setIfResolved();
        this.submitBtn.disabled = false;
        this.enableReviewFields();
    }

    enableReviewFields() {
        if (!this.ticketform) return;
        this.enableFields(['review-notes', 'status']);
        sunEditorClass.enableSingleEditor('review-notes');
    }

    setIfClosed() {
        this.emailLink?.removeAttribute('data-bs-toggle');
        if (this.phoneLink) {
            this.phoneLink.disabled = true;
            this.phoneLink.href = 'javascript:void(0)';
        }
        this.parentIdBtn?.classList.add('disabled');
        this.disableFormElements();
    }

    enableFields(fieldIds) {
        fieldIds.forEach(fieldId => {
            const fieldElement = this.getById(fieldId, false);
            if (fieldElement) {
                fieldElement.disabled = false;
            }
        });
    }

    enableButtons(buttons) {
        buttons.forEach(btn => {
            if (btn) {
                btn.disabled = false;
            }
        });
    }

    disableFormElements() {
        if (!this.ticketform) return;

        const skipElements = new Set(['csrf_token', 'ticket-number', 'ticket-type', 'review-notes']);

        Array.from(this.ticketform.elements).forEach(element => {
            if (!element.closest('.modal') && element.id && !skipElements.has(element.id)) {
                this.disableElement(element);
            }
        });

        tomSelectInstances.forEach(field => {
            const fieldElement = this.getById(field.input.id, false);
            if (fieldElement) {
                field.lock();
            }
        });

        sunEditorClass.disableAllEditors();

        [this.childBtn, this.source].forEach(btn => {
            if (btn) btn.disabled = true;
        });
    }

    disableElement(element) {
        if (element.type === 'checkbox') {
            element.addEventListener('click', e => e.preventDefault());
            element.style.pointerEvents = 'none';
            element.style.cursor = 'not-allowed';
            element.disabled = true;
        } else if (element.type === 'radio') {
            element.disabled = true;
        } else if (element.type === 'button') {
            element.disabled = true;
            element.style.cursor = 'not-allowed';
        } else {
            element.readOnly = true;
            element.style.cursor = 'not-allowed';
            element.disabled = false;
        }
    }
}

export const fieldStatusClass = new FieldStatusClass();
