import {formValidationListener} from '../../../../../static/js/includes/validate-form.js';
import {getSubCategories} from '../../../../../static/js/includes/sub-category.js';
import {initaliseTomSelectFields, tomSelectInstances} from '../../../../../static/js/includes/tom-select.js';
import {sunEditorClass} from '../../../../../static/js/includes/suneditor-class.js';
import {handleMeButton} from '../portal-common.js';

export class PortalMyTickets {
    constructor() {
        this.cancelBtn = document.getElementById('cancel-btn');
        this.category = document.getElementById('category-id');
        this.detailsEditor = sunEditorClass.createSunEditor('details');
        this.form = document.getElementById('form');
        this.impact = document.getElementById('priority-impact');
        this.lowImpactBtn = document.getElementById('single-user');
        this.lowUrgenycyBtn = document.getElementById('user-low');  // low urgency btn
        this.priority = document.getElementById('priority');
        this.shortDesc = document.getElementById('short-desc');
        this.requestedByBtn = document.getElementById('requested-by-btn');
        this.subCategory = document.getElementById('subcategory-id');
        this.submitBtn = document.getElementById('submit-btn');
        this.ticketType = document.getElementById('ticket-type');
        this.urgency = document.getElementById('priority-urgency')
        this.userImpact = 'low';
        this.userImpactBtns = document.querySelectorAll('input[name=\'user-impact\']');
        this.userImpactInfo = document.getElementById('user-impact-info');
        this.userUrgency = 'low';
        this.userUrgencyBtns = document.querySelectorAll('input[name=\'user-priority\']');
        this.userUrgencyInfo = document.getElementById('user-urgency-info');

    }

    async init() {
        // initaliseTomSelectFields(); // set Select fields to Tom-Selects
        formValidationListener();
        this.setupListeners();
        await handleMeButton(); // preset requested_by to current user
        this.setUrgency();
        this.setImpact();
        await this.setSla();
    }

    setupListeners() {
        this.cancelBtn.addEventListener('click', async () => {
            await this.clearForm();
        })

        this.category.addEventListener('change', async () => {
            const category = this.category.options[this.category.selectedIndex].value
            if (category !== '') {
                this.subCategory.disabled = false
            }
            await getSubCategories(category)
        });

        for (const priorityBtn of this.userUrgencyBtns) {
            priorityBtn.addEventListener('click', async () => {
                this.userUrgency = priorityBtn.value
                this.setUrgency();
                await this.setSla()
            })
        }

        for (const impactBtn of this.userImpactBtns) {
            impactBtn.addEventListener('click', async () => {
                this.userImpact = impactBtn.value;
                this.setImpact();
                await this.setSla();
            })
        }

        this.requestedByBtn.addEventListener('click', async () => {
            await handleMeButton();
        })

        this.subCategory.addEventListener('change', async () => {
            await this.getTicketType()
        })

        this.submitBtn.addEventListener('click', () => {
            this.detailsEditor.save();
            this.form.dispatchEvent(new Event('submit'));
        })
    }

    setUrgency() {
        if (this.userUrgency === 'low') {
            this.userUrgencyInfo.innerHTML = 'I can work but need support'
        } else if (this.userUrgency === 'medium') {
            this.userUrgencyInfo.innerHTML = 'Work is disrupted - help ASAP'
        } else {
            this.userUrgencyInfo.innerHTML = 'I cannot work - help urgently'
        }
        this.urgency.value = this.userUrgency
    }

    setImpact() {
        if (this.userImpact === 'low') {
            this.userImpactInfo.innerHTML = 'This only affects me'
        } else if (this.userImpact === 'medium') {
            this.userImpactInfo.innerHTML = 'This affects a Team'
        } else {
            this.userImpactInfo.innerHTML = 'This affects a Department'
        }
        this.impact.value = this.userImpact
    }

    async setSla() {
        // const now = DateTime.now().toFormat('yyyy-MM-dd\'T\'HH:mm');

        const apiArgs = {
            'urgency': this.userUrgency,
            'impact': this.userImpact,
        }

        const response = await fetch('/api/sla/get-sla-priority-from-urgency-impact/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(apiArgs)
        })

        const data = await response.json()

        if (!response.ok) {
            await showSwal('Error', data['error'], 'error');
            return;
        }
        this.priority.value = data['priority'];
        this.setPriorityColour();
    }

    setPriorityColour() {
        this.priority.classList.remove(
            'p-colour-p1',
            'p-colour-p2',
            'p-colour-p3',
            'p-colour-p4',
            'p-colour-p5'
        );

        const priorityClassMap = {
            P1: 'p-colour-p1',
            P2: 'p-colour-p2',
            P3: 'p-colour-p3',
            P4: 'p-colour-p4',
            P5: 'p-colour-p5',
            CR1: 'p-colour-p1',
            CR2: 'p-colour-p2',
            CR3: 'p-colour-p3',
            CR4: 'p-colour-p4',
        };

        this.priority.classList.add(priorityClassMap[this.priority.value]);
    }


    async getTicketType() {
        this.tomSelect = await tomSelectInstances.get(this.subCategory.id);
        const subcat = this.tomSelect.getValue();
        if (!subcat) { // data loads so triggers a 'change' event but nothing selected yet
            return;
        }

        const response = await fetch(`/api/get-ticket-type/?subcat=${subcat}`)
        const data = await response.json()

        if (!response) {
            await showSwal('Error', data['error'])
        } else {
            console.log(data['ticket-type'])
            this.ticketType.value = data['ticket-type']
            console.log(this.ticketType.value)
        }

    }

    async clearForm() {
        this.shortDesc.value = '';
        const tomCat = await tomSelectInstances.get(this.category.id);
        tomCat.clear();
        this.lowImpactBtn.checked = true;
        this.lowUrgenycyBtn.checked = true;
        this.priority.value = 'P5';
        this.urgency.value = 'low';
        this.impact.value = 'low';
        sunEditorClass.clearSunEditorContent('details');
        this.setPriorityColour()
    }
}