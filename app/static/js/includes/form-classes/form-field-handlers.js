import {sunEditorClass} from '../suneditor-class.js';
import {setSliderInitial} from '../utils.js';
import {fetchSupportAgents} from '../support-agents.js';
import {getSubCategories} from '../sub-category.js';
import {tomSelectInstances} from '../tom-select.js';
import {showFormButtons} from './form-utils.js';

class FormFieldHandlerClass {
    constructor() {
        this.category = document.getElementById('category-id');

        // various date time options - just date, just time, or both
        this.dateTimeFields = document.querySelectorAll('.picker-datetime');
        this.dateFields = document.querySelectorAll('.picker-date');
        this.timeFields = document.querySelectorAll('.picker-only-time');

        this.formVars = document.getElementById('form-vars');
        this.existsString = this.formVars.dataset.exists;
        // Parse the string to a boolean
        this.exists = this.existsString === 'true'

        this.form = document.getElementById('form');
        this.formFields = document.querySelectorAll('.dirty');  // fields to store have class .dirty

        this.supportTeam = document.getElementById('support-team');
        this.supportAgents = document.getElementById('support-agent');

        this.storedFieldValues = {};
        this.subCategory = document.getElementById('subcategory-id');
        this.ticketType = document.getElementById('ticket-type');
        this.ticketTypeText = document.getElementById('ticket-type-text');
    }

    async init() {
        this.setupListeners();
        await this.setDateTimePickers();
        await this.storeCurrentValues(); // store current values in case cancel btn is clicked, so we can roll back
        this.form.addEventListener('input', (event) => this.handleFieldInput(event));
        // this.ticketType.classList.add('type-' + this.ticketType.value.toLowerCase().replace(' ', '-'));

    }

    setupListeners() {
    }

    setDateTimePickers() {
        this.dateTimeFields.forEach(field => {
            if (field.id === 'cab-date') {
                flatpickr(field, {
                    altInput: false,  // avoids using a visually separate input
                    theme: 'material-blue',
                    enableTime: true,
                    dateFormat: 'Y-m-d H:i',
                    minDate: 'today',
                    defaultHour: 9,
                    defaultMinute: 0,
                    disable: [
                        function (date) {
                            // return true to disable
                            return (
                                date.getDay() === 0 ||
                                date.getDay() === 1 ||
                                date.getDay() === 3 ||
                                date.getDay() === 5 ||
                                date.getDay() === 6
                            );
                        }
                    ],
                    locale: {
                        'firstDayOfWeek': 1 // start week on Monday
                    }
                });
            } else {
                flatpickr(field, {
                    theme: 'material-blue',
                    enableTime: true,
                    dateFormat: 'Y-m-d H:i',
                    minDate: 'today',
                    defaultHour: 9,
                    defaultMinute: 0,
                });
            }
        });

        this.dateFields.forEach(field => {
            flatpickr(field, {
                enableTime: false,
                dateFormat: 'Y-m-d',
                minDate: 'today',
            });
        });

        this.timeFields.forEach(field => {
            flatpickr(field, {
                enableTime: true,
                noCalendar: true,
                dateFormat: 'H:i',
                minDate: 'today',
            });
        });
    }

    // Store field values for restoring if cancel btn is clicked,
    // this is also useful for noting changes to fields in the journal.
    async storeCurrentValues() {
        const inputs = this.formFields;

        for (let i = 0; i < inputs.length; i++) {
            const field = inputs[i];
            if (field.tagName === 'INPUT') {
                if (field.type === 'range') {
                    this.storedFieldValues[field.id] = field.value;
                } else if (field.type === 'checkbox') {
                    field.addEventListener('click', () => {
                        // Store inverse of state because clicking changes from the original which we need to restore to
                        this.storedFieldValues[field.id] = !field.checked;
                    });
                } else if (field.type === 'radio') {
                    this.storedFieldValues[field.id] = field.checked;
                } else {
                    field.addEventListener('focus', () => {
                        this.storedFieldValues[field.id] = field.value;
                    });
                }
            } else {
                // Retrieve the TomSelect instance from the tomSelectInstances map
                const tomSelect = tomSelectInstances.get(field.id);

                if (tomSelect) {
                    tomSelect.on('focus', () => {
                        const val = tomSelect.getValue();
                        this.storedFieldValues[field.id] = Array.isArray(val) ? val : [val];
                    });
                }
            }
        }

        sunEditorClass.sunEditorInstances.forEach((editorInstance, instanceId) => {
            // Attach focus event listener to the current editor instance
            editorInstance.onFocus = () => {
                // Save the contents of the editor when it gains focus
                this.storedFieldValues[instanceId] = editorInstance.getContents();
            };
        });

    }


    restoreFieldValues() {
        Object.entries(this.storedFieldValues).forEach(([key, value]) => {
            const field = document.querySelector(`#${key}`);
            if (field) {
                // Handle SunEditor instances
                sunEditorClass.sunEditorInstances.forEach((editorInstance, instanceId) => {
                    if (field.id === instanceId) {
                        field.value = value;
                        editorInstance.setContents(field.value);
                    }
                });


                // Handle input fields
                if (field.tagName === 'INPUT') {
                    if (field.type === 'range') {
                        // Restore range input value and update its label
                        field.value = value;
                        const rangelabel = (field.id === 'change-downtime')
                            ? document.querySelector('#downtime-slider-label')
                            : document.querySelector('#duration-slider-label');
                        setSliderInitial(field, rangelabel, field.id === 'change-downtime' ? '#ff0000' : '#0414f4');
                    } else if (field.type === 'checkbox' || field.type === 'radio') {
                        field.checked = value;
                        if (field.type === 'radio' && field.name === 'priority-matrix') {
                            field.click();
                        }
                    } else {
                        field.value = value; // For text inputs
                    }
                }
                // Handle TomSelect fields
                else {
                    const tomSelect = tomSelectInstances.get(field.id);
                    if (tomSelect) {
                        const storedValue = this.storedFieldValues[field.id];
                        if (Array.isArray(storedValue)) {
                            tomSelect.clear();
                            storedValue.forEach(item => tomSelect.addItem(item));
                        } else {
                            tomSelect.setValue(storedValue);
                        }
                    }
                }
            }
        });
    }

    async handleFieldInput(event) {
        switch (event.target.id) {
            case 'support-team':
                await this.supportTeamChange();
                break;
            case 'support-agent':
                this.supportAgentChange();
                break;
            case 'category-id':
                await this.categoryChange();
                break;
            case 'subcategory-id':
                await this.subCategoryChange();
                break;
            default:
                if (event.target.classList.contains('dirty')) this.dirtyField();
        }
    }

    async supportTeamChange() {
        this.dirtyField();
        await fetchSupportAgents(this.supportTeam.options[this.supportTeam.selectedIndex].value);
    }

    supportAgentChange() {
        if (this.supportAgents.options[this.supportAgents.selectedIndex].value) {
            this.dirtyField()
        }
    }

    async categoryChange() {
        if (this.subCategory) {
            await getSubCategories(this.category.value)
        }
        this.dirtyField()
    }

    async subCategoryChange() {
        // Get ticket type (e.g. Incident or Request) upon subcategory change
        if (this.subCategory.value === '') { // when first populated, no sub-cat is selected, so return
            return;
        }

        let response = await fetch(`/api/get-ticket-type/?subcat=${this.subCategory.value}`)
        this.dirtyField()

        let data = await response.json();

        if (!response.ok) {
            await showSwal('Error', data['error'], 'error');
            return
        }
        const ticketType = data['ticket-type']
        if (ticketType) {
            this.ticketType.value = ticketType;
            this.ticketTypeText.textContent = ticketType
            this.dirtyField()
        }
    }


    enableFormElements() {
        // Enables fields with .dirty class (this.formFields)
        const formElements = this.formFields;
        for (let i = 0; i < formElements.length; i++) {
            const field = formElements[i];
            // Retrieve TomSelect instance from the tomSelectInstances map
            const tomSelect = tomSelectInstances.get(field.id);
            if (tomSelect) {
                tomSelect.enable();
            } else if (sunEditorClass.sunEditorInstances.has(field.id)) {
                // Retrieve SunEditor instance from the sunEditorInstances map
                sunEditorClass.sunEditorInstances.get(field.id).enable();
            } else {
                field.disabled = false; // Enable the regular input fields
            }
        }
    }


    dirtyField() {
        showFormButtons();
    }
}

export const formFieldHandlers = new FormFieldHandlerClass();
