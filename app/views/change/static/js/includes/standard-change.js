import {showSwal} from '../../../../../static/js/includes/form-classes/form-utils.js';
import {tomSelectInstances} from '../../../../../static/js/includes/tom-select.js';
import {changeRiskButtonsClass} from './change-risk-buttons-class.js';

export class StandardChangeClass{
    constructor() {
        this.category = document.getElementById('category-id');
        this.changeRisk = document.getElementById('priority');
        this.shortDesc = document.getElementById('short-desc');
        this.templateBtn = document.getElementById('standard-template-btn');
        this.templateId = document.getElementById('standard-template');
    }

    init(){
        this.setupListeners();
        changeRiskButtonsClass.setBtnToRisk();
    }

    setupListeners(){
        this.templateBtn.addEventListener('click', async()=>{
            await this.loadTemplate();
        })
    }

    async loadTemplate(){
        if (!this.templateId.value){
            await showSwal('Error', 'Please select a template', 'error');
            return
        }

        const changeReasonTom = tomSelectInstances.get('change-reason');
        const categoryTom = tomSelectInstances.get('category-id');
        const cmdbIdTom = tomSelectInstances.get('cmdb-id');
        const departmentTom = tomSelectInstances.get('departments-impacted');
        const supportTeamTom = tomSelectInstances.get('support-team');

        const apiArgs = {
            'template-id': this.templateId.value
        }

        const response = await fetch('/api/change/get-standard-template/', {
            method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(apiArgs),
        });

        const data = await response.json()
        if (!response.ok){
            await showSwal('Error Retrieving Template', `${data['error']}`)
        } else {
            changeReasonTom.setValue(data['change-reason']);
            categoryTom.setValue(data['category-id']);
            this.changeRisk.value = data['set-risk'];
            departmentTom.setValue(data['departments-impacted']);
            cmdbIdTom.setValue(data['impacted-ci']);
            this.shortDesc.value = data['short-desc'];
            supportTeamTom.setValue(data['support-team']);
            changeRiskButtonsClass.setBtnToRisk();
        }
    }
}

