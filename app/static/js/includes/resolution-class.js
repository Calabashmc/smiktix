import {sunEditorClass} from './suneditor-class.js';
import {saveNotes, showSwal} from './form-classes/form-utils.js';

export class ResolutionClass {
    constructor() {
        this.currentStep; // set from custom event listener
        this.editResolutionBtn = document.getElementById('btn-edit-resolution');
        this.isParent = document.getElementById('is-parent');

        this.modal = document.getElementById('resolution-modal');
        this.resolutionModal = new bootstrap.Modal(this.modal);

        this.openWorkNoteModalBtn = document.getElementById('open-worknote-modal-btn');
        this.resolutionAddBtn = document.getElementById('modal-add-resolution-btn');
        this.resolutionCancelBtn = document.getElementById('modal-cancel-resolution');
        this.resolutionCode = document.getElementById('resolution-code-id');
        this.resolutionCodeText = document.getElementById('resolution-code-text');

        this.resolvedTab = document.getElementById('resolution-tab');
        this.ticketNumber = document.getElementById('ticket-number');
        this.ticketType = document.getElementById('ticket-type');

        this.status = document.getElementById('status')
    }

    init() {
        this.setupListeners();
    }

    setupListeners() {
        // button on resolution tab to open modal to add to resolution
        this.editResolutionBtn?.addEventListener('click', () => {
            this.resolutionModal.show();
        });

        // add resolution button in modal
        this.resolutionAddBtn.addEventListener('click', () => {
            this.addResolutionHandler()
            // trigger custom event to notify status.js so status can be updated to resolved
            const modalAddResolutionEvent = new CustomEvent('resolutionAdded');
            document.dispatchEvent(modalAddResolutionEvent);
        });

        this.resolutionCancelBtn.addEventListener('click', () => {
            this.resolutionModal.hide();

            const modalCloseEvent = new CustomEvent('resolutionModalClosed');
            document.dispatchEvent(modalCloseEvent);
        });

        // Handle statusStepChange event dispatched from status files
        document.addEventListener('statusStepChange', (event) => {
            this.currentStep = event.detail.step;
            this.openResolutionModal()
        });
    }

    async openResolutionModal() {
        if (this.isParent?.checked || ['Problem', 'Workaround', 'Known Error', 'Change'].includes(this.ticketType.value)) {
            const resolution = await showSwal('', 'Resolving will also resolve any linked child tickets.', 'question');

            if (!resolution.isConfirmed) {
                window.statusClass.goToPriorStep(); // see main class js such as interaction.js
                return false;
            }
        }
        this.resolutionModal.show();
    }

    async addResolutionHandler() {
        const resolutionDetailsEditor = sunEditorClass.sunEditorInstances.get('resolution-notes');
        const resolutionTabJournalEditor = sunEditorClass.sunEditorInstances.get('resolution-journal');
        const isNotBlank = sunEditorClass.checkSunEditorForContent(resolutionDetailsEditor);

        if (!isNotBlank || !this.resolutionCode.value) {
            await showSwal('Blank Resolution', 'Please add a resolution before submitting', 'error');
            return false;
        }

        this.resolutionCodeText.value = this.resolutionCode.options[this.resolutionCode.selectedIndex].text;
        const resolution = resolutionDetailsEditor.getContents();
        // resolutionTabJournalEditor.setContents(resolution);

        const apiArgs = {
            'ticket_number': this.ticketNumber.value,
            'ticket-type': this.ticketType.value,
            'resolution_code_id': this.resolutionCode.value,
            'resolution_notes': resolution,
            'status': this.status.value,
        };

        try {
            const response = await fetch(`/api/save-resolution/`, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(apiArgs),
            });
            const data = await response.json();

            if (response.ok && data.success) {
                this.updateUIAfterResolution();
                await this.setType();
                this.resolutionModal.hide();
                resolutionTabJournalEditor.setContents(data.resolution);
                window.childrenClass.populateChildTicketTable();

            } else {
                await showSwal('Error', data.error, 'error');
            }
        } catch (error) {
            console.error('Error saving resolution:', error);
            await showSwal('Error', error, 'error');
        }
    }

    async updateUIAfterResolution() {
        this.openWorkNoteModalBtn.disabled = true;
        this.resolvedTab.style.display = 'block';
        this.resolvedTab.classList.remove('disabled');

        const resolveTab = new bootstrap.Tab(this.resolvedTab);
        resolveTab.show();

        // add note to both system journal and notes journal
        await saveNotes(`TICKET IS RESOLVED <br> Resolution code is: ${this.resolutionCodeText.value}`, true);
        await saveNotes(`TICKET IS RESOLVED <br> Resolution code is: ${this.resolutionCodeText.value}`);
    }

    async setType() {
        if (this.ticketType.value === 'Problem') {
            const resolutionCodeText = this.resolutionCodeText.value;
            const regex = /Problem|Workaround|Error/i;

            if (regex.test(resolutionCodeText)) {
                this.ticketType.value = resolutionCodeText.includes('Known Error')
                    ? 'Known Error'
                    : 'Workaround';

                const apiArgs = {
                    'ticket-number': this.ticketNumber.value,
                    'ticket-type': this.ticketType.value,
                };

                try {
                    await fetch(`/api/set-type/`, {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify(apiArgs),
                    });
                } catch (error) {
                    console.error('Error updating ticket type:', error);
                }
            }
        }
    }
}
