import {showSwal} from '../../../../static/js/includes/form-classes/form-utils.js';
import {tomSelectInstances} from '../../../../static/js/includes/tom-select.js';

export class ReleaseFormClass {
    constructor() {
        this.addCIsBtn = document.getElementById('add-cis-btn');
        this.approved = document.getElementById('approved');
        this.approvalRequired = document.getElementsByName('approval_by');
        this.buildLeader = document.getElementById('build-leader');
        this.deployLeader = document.getElementById('deployment-leader');

        this.rolesBuildLeader = document.getElementById('roles-build-leader');
        this.rolesTestLeader = document.getElementById('roles-test-leader');
        this.rolesDeployLeader = document.getElementById('roles-deploy-leader');

        this.changeIdBtn = document.getElementById('change-id-btn');
        this.changeIdDiv = document.getElementById('change-id-div');
        this.changeLinkSelect = document.getElementById('change-id');
        this.cisAffected = document.getElementById('affected-cis');
        this.cisSelection = document.getElementById('cis-selection');

        this.productOwnerDiv = document.getElementById('product-owner-div');
        this.removeCIsBtn = document.getElementById('remove-cis-btn');
        this.testLeader = document.getElementById('test-leader');

    }

    init() {
        this.removeSelfFromOptions();
        this.setKeyRoleDisplay();
        this.setApprovalDivs();
        this.setupListeners();
    }

    setupListeners() {
        this.addCIsBtn.addEventListener('click', () => {
            this.handleAddCIs();
        });

        this.removeCIsBtn.addEventListener('click', () => {
            this.handleRemoveCIs();
        });

        this.buildLeader.addEventListener('change', () => {
            this.setKeyRoleDisplay();
        });
        this.testLeader.addEventListener('change', () => {
            this.setKeyRoleDisplay();
        });

        this.deployLeader.addEventListener('change', () => {
            this.setKeyRoleDisplay();
        });

        if (this.approved.checked) {
            this.approved.dataset.locked = 'true';
        }
        this.approved.addEventListener('click', async (e) => {
            await this.handleApprovedTick(e);
        })

        this.approvalRequired.forEach(radio => {
            radio.addEventListener('change', () => {
                if (radio.value === 'CAB' && radio.checked) {
                    this.changeIdDiv.classList.remove('d-none');
                    this.productOwnerDiv.classList.add('d-none');
                } else if (radio.value === 'Product Owner' && radio.checked) {
                    this.productOwnerDiv.classList.remove('d-none');
                    this.changeIdDiv.classList.add('d-none');
                }
            });
        });

        this.changeIdBtn.addEventListener('click', async () => {
            this.handleChangeLink();
        });
    }

    setApprovalDivs() {
        this.approvalRequired.forEach(radio => {
            if (radio.value === 'CAB' && radio.checked) {
                this.changeIdDiv.classList.remove('d-none');
                this.productOwnerDiv.classList.add('d-none');
            } else {
                this.productOwnerDiv.classList.remove('d-none');
                this.changeIdDiv.classList.add('d-none');
            }
        })
    }

    handleAddCIs() {
        const ciTomSelect = tomSelectInstances.get(this.cisSelection.id);
        const selectedOption = ciTomSelect.getValue();
        const selectedText = ciTomSelect.options[selectedOption]?.text;

        if (ciTomSelect && selectedOption) {
            ciTomSelect.clear();
            ciTomSelect.removeOption(selectedOption);
            ciTomSelect.refreshItems();

            const newOption = document.createElement('option');
            newOption.value = selectedOption;
            newOption.text = selectedText;

            this.cisAffected.appendChild(newOption);
            newOption.selected = true;
        }
    };

    handleRemoveCIs() {
        const affectedCiItem = this.cisAffected.options[this.cisAffected.selectedIndex];
        if (affectedCiItem) {
            this.cisAffected.options[this.cisAffected.selectedIndex].remove();

            this.cisSelection.tomselect.addOption({
                value: affectedCiItem.value,
                text: affectedCiItem.text
            })
            this.cisSelection.tomselect.refreshItems();
        }
    };

    async handleApprovedTick(e) {
        if (!this.approved.checked && this.approved.dataset.locked === 'true') {
            // Re-check it and prevent uncheck
            this.approved.checked = true;
            e.preventDefault();
        } else if (this.approved.checked) {
            const response = await showSwal(
                'Approved',
                '<p>Are you sure you want to mark this release as approved? </p><p> Remember to Save the record to retain this change</p>',
                'question',
                true
            )

            if (!response.isConfirmed) {
                this.approved.checked = false;
            } else {
                this.approved.dataset.locked = 'true';
            }
        }
    }

    handleChangeLink() {
        const selectedOption = this.changeLinkSelect.options[this.changeLinkSelect.selectedIndex].text;
        const ticketNumber = selectedOption.split(' | ')[0];
        if (!ticketNumber) {
            return;
        }

        const url = `/ui/change/ticket/normal/?ticket=${ticketNumber}`; // Modify this URL structure as needed
        window.open(url, '_blank');
    }

    removeSelfFromOptions() {
        const cisTomSelect = tomSelectInstances.get('cis-selection');

        if (cisTomSelect) {
            // Collect all affected CIS values (as strings)
            const affectedValues = Array.from(this.cisAffected.options).map(opt => opt.value);

            // Remove these options from cis_selection TomSelect
            affectedValues.forEach(value => {
                cisTomSelect.removeOption(value);
            });

            // Refresh the dropdown
            cisTomSelect.refreshOptions(false);
        }
    }

    setRoles(field, div) {
        const tomSelect = tomSelectInstances.get(field);
        div.textContent = tomSelect.getItem(tomSelect.getValue())?.textContent;
    }

    setKeyRoleDisplay() {
        this.setRoles(this.buildLeader.id, this.rolesBuildLeader);
        this.setRoles(this.testLeader.id, this.rolesTestLeader);
        this.setRoles(this.deployLeader.id, this.rolesDeployLeader);
    }
}