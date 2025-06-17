import {sunEditorClass} from '../suneditor-class.js';
import {formFieldHandlers} from './form-field-handlers.js'
import {tomSelectInstances} from '../tom-select.js';
import {exists, saveNotes, setTodaysDate, showSwal} from './form-utils.js';
import {getCurrentUser} from '../utils.js';

class FormButtonHandlersClass {
    constructor() {
        this.appendedBns = document.querySelectorAll('.input-group-append button');
        this.cancelBtn = document.getElementById('cancel-btn');
        this.commsEmail = document.getElementById('comms-email');
        this.commsJournal = document.getElementById('comms-journal');
        this.email = document.getElementById('email');
        this.emailModal = document.getElementById('send-email-modal');
        this.emailRequesterLink = document.getElementById('email-requester-link');
        this.emailRequesterBtn = document.getElementById('email-requester-btn');
        this.emailSubject = document.getElementById('email-subject');
        this.form = document.getElementById('form');
        this.model = document.getElementById('form-vars').dataset.model;
        this.modalAddNoteOkBtn = document.getElementById('modal-add-worknote-btn');
        this.modalWorknoteCancelBtn = document.getElementById('modal-worknote-cancel-btn');
        this.newFormBtn = document.getElementById('new-form-btn');
        this.nextTicketBtn = document.getElementById('next-btn');
        this.previousTicketBtn = document.getElementById('previous-btn');
        this.path = location.pathname;
        this.requestedBy = document.getElementById('requested-by');
        this.submitBtn = document.getElementById('submit-btn');
        this.supportAgent = document.getElementById('support-agent');
        this.supportAgentBtn = document.getElementById('support-agent-btn')
        this.supportTeam = document.getElementById('support-team');
        this.status = document.getElementById('status');
        this.ticketNumber = document.getElementById('ticket-number');
        this.updates = [];
    }

    init() {
        this.setupListeners()
    }

    setupListeners() {
        this.appendedBns.forEach(btn => {
            btn.addEventListener('click', (e) => {
                const input = e.target.closest('.input-group-append')?.previousElementSibling;
                if (input && ['date', 'datetime', 'datetime-local'].includes(input.type)) {
                    setTodaysDate(input.id);
                    console.log('Found input of type:', input.type);
                }
            })
        })


        this.cancelBtn.addEventListener('click', async () => {
            await this.handleCancelBtn()
        });

        this.submitBtn.addEventListener('click', async (e) => {
            await this.handleSubmitBtn(e)
        });

        this.nextTicketBtn.addEventListener('click', async () => {
            await this.handleNextTicketBtn()
        })

        this.newFormBtn.addEventListener('click', async () => {
            await this.handleNewFormBtn();
        })

        this.previousTicketBtn.addEventListener('click', async () => {
            await this.handlePreviousTicketBtn();
        })

        this.emailRequesterLink?.addEventListener('click', async () => {
            if (!exists) {
                await showSwal('Ticket not saved yet', 'Please save your ticket before sending an email', 'warning');
            } else {
                if (this.email.value.includes('@')) {
                    this.commsEmail.value = this.email.value;
                    new bootstrap.Modal(this.emailModal).show();
                }
            }
        })

        this.emailRequesterBtn?.addEventListener('click', async () => {
            await this.handleEmailRequesterBtn();
        })

        this.modalWorknoteCancelBtn.addEventListener('click', () => {
            this.hideFormButtons();
        })

        this.modalAddNoteOkBtn?.addEventListener('click', async () => {
            await this.handleModalAddNoteOkBtn();
        })

        this.supportAgentBtn?.addEventListener('click', async () => {
            await this.setAgentToUser();
        })
    }


    hideFormButtons() {
        this.submitBtn.hidden = true;
        this.cancelBtn.hidden = true;
    }

    async handleCancelBtn() {
        await formFieldHandlers.restoreFieldValues();
        this.hideFormButtons();
    }

    async handleSubmitBtn(e) {
        e.preventDefault(); // Prevent default form submission
        if (exists) {
            this.updates.push(`Ticket saved <br>`);
            this.updates.push(`The following fields have changed: <br>`)
            Object.entries(formFieldHandlers.storedFieldValues).forEach(([key]) => {
                this.updates.push(`${key}<br>`)
            })
            await saveNotes(this.updates, true);
        }

        if (this.requestedBy) {
            const requestedByTomSelect = tomSelectInstances.get(this.requestedBy.id);
            if (requestedByTomSelect) {
                requestedByTomSelect.enable();
            }
        }


        // Enable form elements to save changes as some elements disabled depending on status
        formFieldHandlers.enableFormElements();

        sunEditorClass.sunEditorInstances.forEach((editor, key) => {
            editor.save();
        });
        // Dispatch the submit event instead of calling form.submit() so that the form validation can be triggered
        // the listener for the submit event is in validate-form.js
        this.form.dispatchEvent(new Event('submit'));
    }

    async handleNewFormBtn() {
        if (['CI'].includes(this.model)) {
            // define radio button options
            const inputOptions = {
                hardware: 'Hardware',
                software: 'Software',
                service: 'Service'
            };

            const {value: ciType} = await Swal.fire({
                title: 'Select a CI type to create',
                input: 'radio', // Built-in input type
                inputOptions,   // Object defining options
                showCancelButton: true,
                inputValue: 'hardware',
                inputValidator: (value) => {
                    if (!value) {
                        return 'You need to choose something!'; // Validation if no selection
                    }
                }
            });

            if (ciType) {
                location.replace(`/ui/cmdb/ticket/${ciType}/?ci_type=${ciType}`)
            }
        } else {
            location.replace(this.path)
        }
    }

    async handleNextTicketBtn() {
        if (!this.ticketNumber) {
            await showSwal('Not saved', 'Ticket has not been saved yet so has not siblings', 'info');
            return;
        }
        const siblings = await this.getSiblingTickets()
        const next = siblings['next'];
        if (next) {
            location.replace(this.path + `?ticket=${next}`)
        } else {
            await showSwal('Nothing beyond', 'I am Omega, the last of my kind', 'info');
        }
    }

    async handlePreviousTicketBtn() {
        if (!this.ticketNumber) {
            await showSwal('Not Saved', 'Ticket has not been saved yet so has no siblings', 'info');
            return;
        }
        const siblings = await this.getSiblingTickets()
        const previous = siblings['previous']
        if (previous) {
            location.replace(this.path + `?ticket=${previous}`)
        } else {
            await showSwal('Nothing prior', 'I am Alpha, there are none before me!', 'info');
        }
    }

    async getSiblingTickets() {
        const apiArgs = {
            'ticket_number': this.ticketNumber.value,
            'model': this.model,
        }

        try {
            const response = await fetch('/api/get_sibling_tickets/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(apiArgs)
            });

            const data = await response.json()

            return {'next': data['next'], 'previous': data['previous']}
        } catch (error) {
            console.error('Error fetching or parsing data:', error);
        }
    }

    async handleModalAddNoteOkBtn() {
        const worklogEditor = sunEditorClass.sunEditorInstances.get('worklog');
        const isNotBlank = sunEditorClass.checkSunEditorForContent(worklogEditor);

        if (isNotBlank) {
            let contents = worklogEditor.getContents()
            await saveNotes(contents);
            worklogEditor.setContents(''); //blank editor

            // note is saved so hide form save/cancel btns
            this.hideFormButtons();
        } else {
            const response = await showSwal('Blank Work Note', 'Please add a note before submitting', 'error');
            if (response.isConfirmed) {
                const workNoteModal = document.getElementById('workNoteModal');
                new bootstrap.Modal(workNoteModal).show();
            }
        }
    }

    async handleEmailRequesterBtn() {
        const response = await fetch('/api/send_requester_email/',
            {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    'ticket_number': this.ticketNumber.value,
                    'ticket_type': this.model,
                    'subject_line': this.emailSubject.value,
                    'body_text': this.commsJournal.value || 'No body text',
                })
            })

        if (!response.ok) {
            const errorData = await response.json();
            console.error('Error:', errorData);
            await showSwal('Error', errorData.error || 'Requester email could not be sent', 'error');
        }
    }

    async setAgentToUser(fieldId) {
        const userDetails = await getCurrentUser();
        const tomSelectTeamInstance = tomSelectInstances.get(this.supportTeam.id)

        tomSelectTeamInstance.setValue(userDetails['user_team_id']);

        const tomSelectAgentInstance = tomSelectInstances.get(this.supportAgent.id)

        // Wait for a short time before setting the agent to allow for the select to populate based on the team
        setTimeout(() => {
            tomSelectAgentInstance.setValue(userDetails['user_id']);
        }, 400); // Adjust the delay if needed
    }
}

export const formButtonHandlers = new FormButtonHandlersClass();