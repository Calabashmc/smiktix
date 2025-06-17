import {saveNotes, showSwal} from '../../../../../static/js/includes/form-classes/form-utils.js';

class SlaClass {
    constructor() {
        this.modalPauseCancelBtn = document.getElementById('modal-pause-cancel-btn');
        this.modalPauseSLABtn = document.getElementById('modal-pause-sla-btn');

        this.pauseHistory = document.getElementById('pause-history');
        this.pauseReason = document.getElementById('sla-pause-reason');
        this.modal = document?.getElementById('slaPauseReasonModal');

        this.priority = document.getElementById('priority');
        this.priorityImpact = document.getElementById('priority-impact');
        this.priorityUrgency = document.getElementById('priority-urgency');

        this.respondedCheck = document.getElementById('responded-check'); // span for check of cross
        this.resolvedCheck = document.getElementById('resolved-check'); // span for check of cross

        this.slaFace = document?.getElementById('sla-face');
        if (this.slaFace) { // because slaface not used in admin but this class is
            this.slaFaceBaseUrl = this.slaFace.getAttribute('data-base-url');
        }

        this.slaPaused = document.getElementById('sla-paused');
        this.slaPauseBtn = document.getElementById('sla-pause-btn');
        this.slaResolveBy = document.getElementById('sla-resolve-by');
        this.slaResolveText = document.getElementById('sla-resolve-text');
        this.slaResponseBreach = document.getElementById('sla-response-breach');
        this.slaRespondBy = document.getElementById('sla-respond-by');
        this.slaRespondText = document.getElementById('sla-respond-text');
        this.slaResolveBreach = document.getElementById('sla-resolve-breach');

        this.ticketNumber = document.getElementById('ticket-number');
    }

    async init() {
        this.setupListeners();
        await this.checkIfPaused();
        await this.setSlaIndicators()
        await this.displayPauseHistory();
        if (this.modal) {
            this.pauseReasonModal = new bootstrap.Modal(this.modal);
        }
    }

    setupListeners() {
        // cancel button in the Pause Reason Modal
        this.modalPauseCancelBtn.addEventListener('click', () => {
            this.pauseReasonModal.hide();
            this.slaPaused.checked = false; // uncheck the pause checkbox
        })

        // OK Button in the Pause Reason Modal. Set SLA Pause Reason
        this.modalPauseSLABtn.addEventListener('click', async () => {
            if (this.pauseReason.value !== '') {
                await this.pauseSla()
            } else {
                this.slaPaused.checked = false; // uncheck the pause checkbox
                await showSwal('Oops...', 'Valid pause reason not selected', 'error');
            }
            this.pauseReasonModal.hide();
        })

        // If checked Show the modal to set Pause Reason if the SLA is not breached else resume the SLA
        this.slaPaused.addEventListener('click', async (event) => {
            console.log(event.target.checked)
            if (this.slaResponseBreach.checked && event.target.checked) {
                event.preventDefault(); // don't set button to clicked
                await showSwal('Oops...', 'You cannot pause a ticket with a breached SLA!', 'error');
            } else {
                if (event.target.checked) {
                    // open modal to select a Pause Reason. Action on buttons listeners above
                    this.pauseReasonModal.show();
                } else {
                    await this.slaTimerResume();
                }
            }
        });
    }

    // Called from interaction-priority-button-class.js to update SLA details
    async setSlaDetails() {
        const apiArgs = {
            impact: this.priorityImpact.value,
            urgency: this.priorityUrgency.value,
            priority: this.priority.value,
            ticket_number: this.ticketNumber.value,
        };

        const response = await fetch(`/api/sla/set-sla-details/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(apiArgs),
        })

        const data = await response.json()

        if (!response.ok) {
            await showSwal('Error', `Unable to check SLA status ${data.error}`, 'error');
        } else {
            const respond_by = data['respond-by'];
            const resolve_by = data['resolve-by'];

            this.slaRespondText.innerHTML = respond_by;
            this.slaResolveText.innerHTML = resolve_by;
            this.slaResponseBreach.checked = data['respond-breach']; // convert 'true' or 'false' to boolean
            this.slaResolveBreach.checked = data['resolve-breach'];
            this.setSlaIndicators()
            await saveNotes(`Priority changed to: ${this.priority.value} - Impact: ${this.priorityImpact.value} - Urgency: ${this.priorityUrgency.value}`, true);
        }
    }


    setSlaIndicators() {
        this.respondedCheck.innerHTML = '<i class="h5 bi bi-check2-circle"></i>'
        this.resolvedCheck.innerHTML = '<i class="h5 bi bi-check2-circle"></i>'
        this.slaFace.src = this.slaFaceBaseUrl + 'happy.svg';

        if (this.slaResponseBreach.checked) {
            this.respondedCheck.innerHTML = '<i class="h5 bi bi-x-circle"></i>';
            this.slaFace.src = this.slaFaceBaseUrl + 'scared.svg';
        }

        if (this.slaResponseBreach.checked && this.slaResolveBreach) {
            this.respondedCheck.innerHTML = '<i class="h5 bi bi-x-circle"></i>';
            this.resolvedCheck.innerHTML = '<i class="h5 bi bi-x-circle"></i>';
            this.slaFace.src = this.slaFaceBaseUrl + 'frustrated.svg';
        }
    }

    //
    async pauseSla() {
        const apiArgs = {
            ticket_number: this.ticketNumber.value,
            pause_reason: this.pauseReason.value,
        };

        const response = await fetch(`/api/sla/pause-sla/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(apiArgs),
        })
        const data = await response.json();
        if (response.ok) {
            let pause_text = this.pauseReason.options[this.pauseReason.selectedIndex].text;
            await saveNotes(`SLA Paused: ${pause_text}`);
            await saveNotes(`SLA Paused: ${pause_text}`, true);

            await this.checkIfPaused(); // to set the images and pause button to paused
            await this.displayPauseHistory();
        } else {
            await showSwal('Error', data['error'], 'error');
        }
    }


    async slaTimerResume() {
        const apiArgs = {
            ticket_number: this.ticketNumber.value,
        };

        const response = await fetch(`/api/sla/resume-sla/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(apiArgs),
        })
        const data = await response.json();
        if (response.ok) {
            await saveNotes('SLA Timer Resumed');
            await saveNotes('SLA Timer Resumed', true);
            await this.checkIfPaused(); // to set the images and pause button to paused
            await this.displayPauseHistory();
        } else {
            await showSwal('Error', data['error'], 'error');
        }
    }


    // changes the SLA Pause button to either Pause or Resume. Also changes the SLA image to snoozing if paused
    async checkIfPaused() {
        if (this.slaPaused.checked) {
            this.slaFace.src = this.slaFaceBaseUrl + 'paused.svg';
            this.slaPauseBtn.innerHTML = '<i class="h2 bi bi-play-fill"></i><span class="d-flex align-items-center">Resume SLA</span>'
            this.slaPauseBtn.classList.replace('btn-danger', 'btn-warning');
        } else {
            this.setSlaIndicators();
            this.slaPauseBtn.innerHTML = '<i class="h2 bi bi-pause-fill"></i><span class="d-flex align-items-center">Pause SLA</span>'
            this.slaPauseBtn.classList.replace('btn-warning', 'btn-danger');
        }
    }

    // displays a journal of pause history on the info tab under the pause button
    async displayPauseHistory() {
        try {
            const response = await fetch('/api/sla/get-sla-pause-history/', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({'ticket-number': this.ticketNumber.value}),
            });

            const data = await response.json();
            this.pauseHistory.innerHTML = '';  // clear existing pause history entries else there will be multiple copies

            if (response.ok) {
                if (data['info']) { // no pause history
                    this.pauseHistory.innerHTML = data['info'];
                } else if (data['error']) {
                    await showSwal('Error', data['error'], 'error');
                } else {
                    // Generate HTML from pause history array
                    for (const ph of data['pause_history']) {
                        const entry = document.createElement('p');
                        entry.innerHTML = `Paused: ${ph.paused_at} <br> By: ${ph.paused_by}<br>Resumed: ${ph.resumed_at}<br>Duration: ${ph.duration} mins<br> Reason: ${ph.reason}`;
                        this.pauseHistory.appendChild(entry);
                    }
                }
            }
        } catch (error) {
            console.error('Error fetching pause history:', error);
        }
    }
}

export const slaClass = new SlaClass();