import {saveNotes, showSwal} from '../../../../../static/js/includes/form-classes/form-utils.js';

export class ParentClass {
    constructor() {
        this.childrenTab = document.getElementById('children-tab');
        this.childrenTabPane = document.getElementById('children-tab-pane');
        this.detailsTab = document.getElementById('details-tab');
        this.detailsTabPane = document.getElementById('details-tab-pane');

        this.formVars = document.getElementById('form-vars');
        this.existsString = this.formVars.dataset.exists;
        // Parse the string to a boolean
        this.exists = this.existsString === 'true'

        this.isParent = document.getElementById('is-parent');
        this.isParentlabel = document.querySelector('label[for="is-parent"]');
        this.parent = document.getElementById('ticket-number');
        this.parentDetailsDiv = document.getElementById('parent-details'); // for new ticket this is hidden
        this.parentIdBtn = document.getElementById('parent-id-btn');
        this.parentIdCancelBtn = document.getElementById('modal-cancel-parent-id-btn');
        this.parentIdSetBtn = document.getElementById('modal-set-parent-id-btn');
        this.parentModal = document.getElementById('parent-modal');

        this.parentIdModal = new bootstrap.Modal(this.parentModal);
        this.parentNumber = document.getElementById('parent-number'); //span to display parent ID

        this.parentSelect = document.getElementById('parent-id');
        this.ticketNumber = document.getElementById('ticket-number');
        this.ticketType = document.getElementById('ticket-type');  // the type should be Incident, Request, Problem, or Change
    }

    async init() {
        if (this.exists) {
            this.parentDetailsDiv.classList.remove('d-none');
        }
        await this.setupListeners();
        this.displayParentLink();
    }

    async setupListeners() {
        this.isParent.addEventListener('click', () => {
            this.isParentCheck()
        })

        this.parentSelect?.addEventListener('change', () => {
            this.parentIdSetBtn.classList.remove('disabled');
        })

        this.parentIdBtn?.addEventListener('click', () => {
            this.parentIdModal.show();
        });

        this.parentIdSetBtn?.addEventListener('click', () => {
            this.setParent();
        });

        this.parentIdCancelBtn?.addEventListener('click', () => {
            this.parentIdModal.hide();
        });


    }

    async setParent() { // set the parent ID in the parent select
        const parentTicket = this.parentSelect.options[this.parentSelect.selectedIndex].value;
        if (parentTicket !== '') {
            this.parentIdModal.hide();
            await this.saveParent(parentTicket);
        } else {
            const response = await showSwal(
                'Are you sure?',
                'Selecting None will clear the Parent ID and remove any relationships to other tickets if they exist.',
                'question'
            );
            if (response.isConfirmed) {
                this.parentIdModal.hide()
                await this.unlinkFromParent();
            }
        }
    }

    async isParentCheck() {
        if (this.isParent.checked) {
            const response = await showSwal('Set as Parent?', 'Add child tickets via Relationship tab.', 'question');

            if (response.isConfirmed) {
                await this.setTicketIsParent();
                // activate the children tab
                const relatedTab = new bootstrap.Tab(document.getElementById('children-tab'));
                relatedTab.show(); // This will automatically deactivate the current active tab

                await saveNotes('Set as Parent Ticket', true);

            } else if (result.dismiss === Swal.DismissReason.cancel) {
                this.isParent.checked = false;
            }
        } else {
            await this.removeChildTickets()
        }
    }


    async setTicketIsParent() {
        const response = await fetch('/api/set-as-parent/', // api_incident_problem_functions.py
            {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    'ticket-number': this.ticketNumber.value
                })
            });
        const data = await response.json();

        if (response.ok) {
            this.parentIdBtn.style.display = 'none';
            this.isParent.labels[0].innerHTML = 'Is a Parent';
            // make visible the children tab
            this.childrenTab.classList.remove('disabled');

        } else {
            await showSwal('Error', data['error'], 'error');
        }
    }

    async saveParent(parentTicket) {
        const response = await fetch('/api/set-parent-id/',
            {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    'parent-id': parentTicket,
                    'ticket-number': this.ticketNumber.value
                })
            });
        const data = await response.json();
        if (data['status'] === 'success') {
            await saveNotes(`Tickets parent is set to ${parentTicket}`, true);
            this.displayParentLink()
        } else {
            await showSwal('Error', data['error'], 'error');
        }
    }

    // display a link to the selected parent ticket if it exists, else hide the link
    displayParentLink() {
        const selectedParentOption = this.parentSelect.options[this.parentSelect.selectedIndex];
        const parentTicketText = selectedParentOption.text;

        if (!this.isParent.checked) {
            if (parentTicketText !== 'None') {
                // hide is_parent checkbox and label
                this.isParent.style.display = 'none';
                this.isParentlabel.style.display = 'none';

                const ticket = parentTicketText.replace(/\|.*$/, ''); // need this because in the select we show ticket num and short desc
                const parentUrl = `/ui/interaction/ticket/?ticket=${ticket}`;
                this.parentNumber.style.display = 'block';
                this.parentNumber.innerHTML = `Ticket's parent is <a href='${parentUrl}' target='_blank'>${ticket}</a>`;
            //  disable the children tab
                this.childrenTab.classList.add('disabled');
            }
        } else {
            this.parentIdBtn.style.display = 'none';
            this.isParent.labels[0].innerHTML = 'Is a Parent';

            // make visible the children tab
            this.childrenTab.classList.remove('disabled');
        }
    }


    async removeChildTickets() {
        const response = await fetch('/api/check-for-children/',
            {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    'ticket-number': this.ticketNumber.value
                })
            });

        const data = await response.json();

        if (!response.ok) {
            await showSwal('Error', data['error'], 'error');
        } else {
            const result = await showSwal(
                'Are you sure?',
                `<p><bold>${data['children']} tickets.</bold> will be unlinked</p>`,
                'question'
            );
            if (result.isConfirmed) {
                // this.ticketStandsAlone(); // display ability to set as parent or choose a parent
                await this.removeChildren();
                await saveNotes('Ticket is no longer a Parent.', true)

            } else if (result.dismiss === Swal.DismissReason.cancel) {
                this.isParent.checked = true;
            }
        }
    }

    async ticketStandsAlone() {
        this.isParent.style.display = 'block';
        this.isParentlabel.style.display = 'block';
        this.isParent.checked = false;

        this.parentIdBtn.style.display = 'block';
        this.parentNumber.style.display = 'none'

        // disable the children tab
        this.childrenTab.classList.add('disabled');
        this.childrenTab.classList.remove('active');
        this.childrenTabPane.classList.remove('active', 'show');

        // Set the details tab as active and show so the children tab is hidden. Without this, if the children tab
        // was active, it would still show even though the tab was disabled
        this.detailsTab.classList.add('active', 'show');
        this.detailsTabPane.classList.add('active', 'show');
        // refresh the children table - should be empty so remove all rows
        await window.childrenClass.populateChildTicketTable();
    }

    async removeChildren() {
        const response = await fetch(`/api/remove_children/?parent=${this.parent.value}`)
        const data = await response.json();

        if (response.ok) {
            await showSwal('', 'All Child tickets set to Stand-alone', 'success');
            await saveNotes('Child Tickets disassociated', true);
            await this.ticketStandsAlone();
        } else {
            await showSwal('Error', data['error'], 'error');
        }
    }

    async unlinkFromParent() {
        const response = await fetch('/api/unlink-children/',
            {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    'ticket-number': this.ticketNumber.value,
                    'ticket-type': this.ticketType.value
                })
            });
        const data = await response.json();

        if (!response.ok) {
            await showSwal('Error', data['error'], 'error');
        } else {
            await saveNotes('Ticket is no longer a Parent.', true);
            await this.ticketStandsAlone();
        }
    }
}





