import {visNetworkClass} from '../../../../static/js/includes/vis-network-class.js';
import {tomSelectInstances} from '../../../../static/js/includes/tom-select.js';
import {exists, showSwal} from '../../../../static/js/includes/form-classes/form-utils.js';

class CmdbClass {
    constructor() {
        this.addDownstreamBtn = document.getElementById('add-downstream-btn');
        this.addUpstreamBtn = document.getElementById('add-upstream-btn');
        this.cancelBtn = document.getElementById('cancel-btn');
        this.ciIconSelectBtn = document.getElementById('icon-select-btn');
        this.ciIconSelectBtnImg = document.getElementById('icon-select-btn-img')

        this.ciIconModal = new bootstrap.Modal(document.getElementById('set-icon-modal'));

        this.ciIconModalSaveBtn = document.getElementById('modal-set-icon-btn');
        this.ciIcons = document.getElementById('ci-icons');
        this.ciName = document.getElementById('name');

        this.ciSelectedIcon = document.getElementById('selected-icon');
        this.downstreamNodeSelect = document.getElementById('downstream-node');
        this.downstreamList = document.getElementById('downstream-list');
        this.id = document.getElementById('form-vars').dataset.id;
        this.mode = 'darkMode';
        this.modeCheckbox = document.getElementById('lightSwitch');
        this.network = null;
        this.networkContainer = document.getElementById('network-container');

        this.networkDepth = document.getElementById('network-depth');
        this.networkModalCloseBtn = document.getElementById('network-modal-close-btn');
        this.modalNetworkContainer = document.getElementById('modal-network-container');
        this.openModalBtn = document.getElementById('open-network-modal-btn');

        this.removeDownstreamBtn = document.getElementById('remove-downstream-btn');
        this.removeUpstreamBtn = document.getElementById('remove-upstream-btn');
        this.submitBtn = document.getElementById('submit-btn');
        this.ticketNumber = document.getElementById('ticket-number');
        this.ticketType = document.getElementById('ticket-type');
        this.upstreamList = document.getElementById('upstream-list');
        this.upstreamNodeSelect = document.getElementById('upstream-node');

        this.vendorSalesSelect = document.getElementById('vendor-sales-id');
        this.vendorSupportSelect = document.getElementById('vendor-support-id');
        this.vendorWarrantySelect = document.getElementById('vendor-warranty-id');
    }

    async init() {
        this.setupListeners();
        if (exists) {
            await this.loadCiIcon();
            this.removeSelfFromOptions();
            await visNetworkClass.drawNetwork(this.networkContainer, this.id);
        }
    }

    setupListeners() {
        // Hardware and Software CI's both have Upstream nodes
        // Upstream config
        if (['Hardware', 'Software'].includes(this.ticketType.value)) {
            this.addRemoveNodes({
                addBtn: this.addUpstreamBtn,
                removeBtn: this.removeUpstreamBtn,
                sourceSelect: this.upstreamNodeSelect,
                destinationList: this.upstreamList,
                oppositeSelect: null,
                direction: 'upstream',
                url: '/api/cmdb/save_ci_relationship/'
            });
        }

        // Only Hardware and Service CI's have Downstream nodes
        // Service CI's use Downstream to specify supporting infrastructure
        // Downstream Config
        if (['Hardware', 'Service'].includes(this.ticketType.value)) {
            this.addRemoveNodes({
                addBtn: this.addDownstreamBtn,
                removeBtn: this.removeDownstreamBtn,
                sourceSelect: this.downstreamNodeSelect,
                destinationList: this.downstreamList,
                oppositeSelect: this.ticketType.value === 'Hardware' ? this.upstreamNodeSelect : null,
                direction: 'downstream',
                url: this.ticketType.value === 'Hardware' ? '/api/cmdb/save_ci_relationship/' : '/api/cmdb/save_service_relationships/',
            });
        }

        this.ciIconSelectBtn.addEventListener('click', async () => {
            this.ciSelectedIcon.src = this.ciIconSelectBtnImg.src
            this.ciIcons.addEventListener('change', () => {
                this.ciSelectedIcon.src = this.ciIcons.options[this.ciIcons.selectedIndex].value;
            })
            this.ciIconModal.show();
        })

        this.ciIconModalSaveBtn.addEventListener('click', () => {
            this.ciIconSelectBtnImg.src = this.ciSelectedIcon.src;
            this.ciIconModal.hide()
        })

        this.networkDepth.addEventListener('change', async() => {
            // depth of 1 is just the current CI so depth + 1 will give first level of network
            await visNetworkClass.drawNetwork(this.modalNetworkContainer, this.id, this.networkDepth.value);
        })

        this.networkModalCloseBtn.addEventListener('click', async () => {
            await visNetworkClass.popInNetwork();
        })

        // this is to change font color of vis-network nodes
        this.modeCheckbox.addEventListener('click', async () => {
            await this.getMode();
        })

        //     listener for network diagram modal popout
        this.openModalBtn.addEventListener('click', async () => {
            await visNetworkClass.popOutNetwork();
        })

        this.vendorSalesSelect.addEventListener('change', async () => {
            await this.getVendorDetails(this.vendorSalesSelect, 'Sales')
        });

        this.vendorSupportSelect.addEventListener('change', async () => {
            await this.getVendorDetails(this.vendorSupportSelect, 'Support')
        });

        this.vendorWarrantySelect?.addEventListener('change', async () => {
            await this.getVendorDetails(this.vendorWarrantySelect, 'Warranty')
        });

    }

    removeSelfFromOptions() {
        // Remove CI name from upstream and downstream options
        const removeOptionContainingText = (selectElement, text) => {

            if (tomSelectInstances.has(selectElement.id)) {
                const tomSelectInstance = tomSelectInstances.get(selectElement.id);
                // Find options containing the text and get their values
                const optionsToRemove = Array.from(selectElement.options).filter(option =>
                    option.text.includes(text)
                );
                // Remove each by value using TomSelect method
                optionsToRemove.forEach(option => {
                    tomSelectInstance.removeOption(option.value);
                });
                tomSelectInstance.refreshItems();
            } else if (selectElement) {
                // Fallback if TomSelect isn't initialized
                Array.from(selectElement.options).forEach(option => {
                    if (option.text.includes(text)) {
                        option.remove();
                    }
                });
            }
        }

        const ciNameValue = this.ciName.value;

        // Service is made up of hardware and software so only has downstream nodes
        if (['Hardware', 'Software'].includes(this.ticketType.value)) {
            removeOptionContainingText(this.upstreamNodeSelect, ciNameValue);
        }


        // hardware and service CI's have downstream nodes. Software is installed on hardware so only has upstream
        if (['Hardware', 'Service'].includes(this.ticketType.value) ) {
            removeOptionContainingText(this.downstreamNodeSelect, ciNameValue);
        }

    }

    showFormButtons() {
        this.submitBtn.hidden = false;
        this.cancelBtn.hidden = false;
    }

    addRemoveNodes(config) {
        const {
            addBtn,
            removeBtn,
            sourceSelect,
            destinationList,
            oppositeSelect,
            direction,
            url
        } = config;

        addBtn.addEventListener('click', async () => {
            const node = await this.addNode(sourceSelect, destinationList, oppositeSelect);
            if (node) {
                await this.addRemoveFromDB(node, direction, 'add', url);
            }
        });

        removeBtn.addEventListener('click', async () => {
            const node = await this.removeNode(destinationList, sourceSelect, oppositeSelect);
            if (node) {
                await this.addRemoveFromDB(node, direction, 'remove', url);
            }
        });
    }


    async addNode(sourceSelect, destinationSelect, oppositeSelect) {
        // Get the TomSelect instance from the tomSelectInstances map
        const sourceTomSelect = tomSelectInstances.get(sourceSelect.id);
        const selected = sourceSelect.options[sourceSelect.selectedIndex];

        if (selected && selected.value !== '0') {
            // Remove it from the source select
            sourceTomSelect.clear();
            sourceTomSelect.removeOption(selected.value);
            sourceTomSelect.refreshItems();

            // If oppositeSelect is provided, remove the option from it as well
            if (oppositeSelect) {
                const oppositeTomSelect = tomSelectInstances.get(oppositeSelect.id);
                oppositeTomSelect.clear();
                oppositeTomSelect.removeOption(selected.value);
                oppositeTomSelect.refreshItems();
            }

            // Add the selected option to the destination select
            const newOption = document.createElement('option');
            newOption.value = selected.value;
            newOption.text = selected.text;

            destinationSelect.appendChild(newOption);
            newOption.selected = true;
            return {node_id: selected.value, node_text: selected.text};
        }
        return null; // Return null if no valid option was selected
    }

    async removeNode(sourceSelect, destinationSelect, oppositeSelect) {
        // adds nodes back to select inputs for selection as up or downstream nodes again
        const selected = sourceSelect.options[sourceSelect.selectedIndex];

        if (selected === undefined || selected.value === '0') {
            return null;
        }

        destinationSelect.tomselect.addOption({
            value: selected.value,
            text: selected.text
        })

        if (oppositeSelect) {
            oppositeSelect.tomselect.addOption({
                value: selected.value,
                text: selected.text
            })
        }

        destinationSelect.tomselect.refreshItems()
        sourceSelect.options[sourceSelect.selectedIndex].remove()
        return {node_id: selected.value, node_text: selected.text};
    }

    async addRemoveFromDB(node, direction, action, url) {
        let apiArgs = {
            'ticket_number': this.ticketNumber.value,
            'direction': direction,
            'node': node,
            'action': action,
        }

        try {
            // Send API request
            const response = await fetch(url, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(apiArgs),
            });

            // Parse JSON response
            const data = await response.json();

            if (response.ok && !data.error) {
                // Successfully processed the request
                await visNetworkClass.drawNetwork(this.networkContainer, this.id);

            } else {
                // Display error from server response
                await showSwal('Error', data.error || 'An unexpected error occurred.', 'error');
            }
        } catch (error) {
            // Handle network or unexpected errors
            await showSwal('Error', error.message || 'An unexpected error occurred.', 'error');
        }
    }


    async getVendorDetails(vendorSelect, vendorType) {
        try {
            const id = vendorSelect.value;
            const response = await fetch(`/api/get-vendor-details/?id=${id}`);
            const userData = await response.json();
            // Only update DOM elements if the data has changed
            if (userData) {
                // Dynamically construct the field names
                const contactField = this[`vendor${vendorType}Contact`];
                const emailField = this[`vendor${vendorType}Email`];
                const phoneField = this[`vendor${vendorType}Phone`];

                if (contactField) contactField.value = userData.contact ?? 'Contact unknown';
                if (emailField) emailField.value = userData.email ?? 'Email unknown';
                if (phoneField) phoneField.value = userData.phone ?? 'Phone unknown';
            }
        } catch (error) {
            console.error(error);
        }

        this.showFormButtons();
    }


    async loadCiIcon() {
        const icon = await visNetworkClass.getVisNetworkIcon(this.ticketNumber.value);
        const DIR = visNetworkClass.DIR
        this.ciIconSelectBtnImg.src = `${DIR}${icon}`
    }

    // this is to change font color of vis-network nodes
    async getMode() {
        const modeRadio = document.querySelector('#lightSwitch');
        if (modeRadio.checked === true) {
            this.mode = 'darkMode'
        } else {
            this.mode = 'lightMode'
        }
        await visNetworkClass.drawNetwork(this.networkContainer, this.id)
    }
}

export const cmdbClass = new CmdbClass()

