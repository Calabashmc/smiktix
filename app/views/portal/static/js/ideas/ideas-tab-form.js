import {sunEditorClass} from '../../../../../static/js/includes/suneditor-class.js';
import {initaliseTomSelectFields, tomSelectInstances} from '../../../../../static/js/includes/tom-select.js';
import {handleMeButton} from '../portal-common.js';
import {formValidationListener} from '../../../../../static/js/includes/validate-form.js';
import {showSwal} from '../../../../../static/js/includes/form-classes/form-utils.js';

export class PortalIdeas {
    constructor() {
        this.cancelBtn = document.getElementById('cancel-btn');
        this.category = document.getElementById('category-id')
        this.form = document.getElementById('form');
        this.ideaImageBtn = document.getElementById('idea-img-btn');
        this.shortDesc = document.getElementById('short-desc')
        this.submitBtn = document.getElementById('submit-btn');

    }

    async init() {
        // initaliseTomSelectFields();
        formValidationListener();
        this.initialiseEditors()
        await handleMeButton();
        this.setupListeners()
    }

    initialiseEditors() {
        this.benefitChecks = document.querySelectorAll('input[type="checkbox"][name="benefits"]');
        this.currentIssueEditor = sunEditorClass.createSunEditor('current-issue');
        this.detailsEditor = sunEditorClass.createSunEditor('details');
        this.dependenciesEditor = sunEditorClass.createSunEditor('dependencies');
        this.impactChecks = document.querySelectorAll('input[type="checkbox"][name="impact"]');
        this.requestedByBtn = document.getElementById('requested-by-btn');
        this.risksEditor = sunEditorClass.createSunEditor('risks-challenges');
    }

    setupListeners() {
        this.cancelBtn.addEventListener('click', async () => {
            await this.clearForm();
        })

        this.requestedByBtn.addEventListener('click', async () => {
            await handleMeButton();
        })

        this.submitBtn.addEventListener('click', () => {
            this.submitForm();
        })

        this.ideaImageBtn.addEventListener('click', async () => {
            await showSwal(
                'Help Us Improve',
                '<p>By sumbitting ideas you are helping us to come up with new and innovative ways to improve. </p> ' +
                '<p>Improvement happens with lots of small steps so any ideas are welcome. ' +
                'We just ask that you check so see if a similar idea has already been submitted. If so Up vote it!</p>',
                'info'
            )
        })
    }

    async clearForm() {
        this.shortDesc.value = '';
        await tomSelectInstances.get(this.category.id).clear();
        sunEditorClass.clearSunEditorContent('current-issue');
        sunEditorClass.clearSunEditorContent('details');
        sunEditorClass.clearSunEditorContent('dependencies');
        sunEditorClass.clearSunEditorContent('risks-challenges');
        this.benefitChecks.forEach(benefitCheck => {
            benefitCheck.checked = false;
        })
        this.impactChecks.forEach(impactCheck => {
            impactCheck.checked = false;
        })
    }

    submitForm() {
        this.currentIssueEditor.save();
        this.detailsEditor.save();
        this.dependenciesEditor.save()
        this.risksEditor.save();
        this.form.dispatchEvent(new Event('submit'));
    }

}