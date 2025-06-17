import {VisNetworkClass} from '../../../../static/js/includes/vis-network-class.js';
import {showSwal} from '../../../../static/js/includes/form-classes/form-utils.js';

const visNetworkClass = new VisNetworkClass();

class ChangeImpactClass {
    constructor() {
        this.changeImpact = document.getElementById('change-scale');
        this.changeImpactBtn = document.getElementById('change-scale-btn');
        this.changeType = document.getElementById('change-type')
        this.changeTypeButton = document.getElementById('change-type-btn');
        this.cisImpacted = document.getElementById('cmdb-id');

        // id is passed via route. It will be 'None' for new CI
        this.id = document.getElementById('form-vars').dataset.id;

        this.openModalBtn = document.getElementById('open-network-modal-btn');
        this.modalNetworkContainer = document.getElementById('modal-network-container');
        this.networkDepth = document.getElementById('network-depth');
        this.networkModalCloseBtn = document.getElementById('network-modal-close-btn');

    }

    async init() {
        this.setupListeners();
        if (this.changeType.value === 'Normal') {
            this.setChangeImpactIcons();
        }
        await this.drawImpactMap();
    }

    setupListeners() {
        this.changeImpact?.addEventListener('change', () => {
            this.setChangeImpactIcons();
        });

        this.changeType.addEventListener('change', () => {
            this.setChangeTypeIcons();
        });

        // listen for CI's being added and build network map
        this.cisImpacted.addEventListener('change', async () => {
            await this.drawImpactMap()
        })

        //listener for network diagram modal popout
        this.openModalBtn.addEventListener('click', async () => {
            if (this.cisImpacted.value) {
                await visNetworkClass.popOutNetwork();
            } else {
                await showSwal('No Primary CI', 'Select a Primary CI to draw the impact map', 'info');
            }
        });

        this.networkDepth.addEventListener('change', async () => {
            // depth of 1 is just the current CI so depth + 1 will give first level of network
            await visNetworkClass.drawNetwork(this.modalNetworkContainer, this.id, this.networkDepth.value);
        })

        this.networkModalCloseBtn.addEventListener('click', async () => {
            await visNetworkClass.popInNetwork();
        })
    }


    setChangeImpactIcons() {
        switch (this.changeImpact.value) {
            case 'Minor':
                this.changeImpactBtn.innerHTML = '<i class=\'bi bi-thermometer ms-auto text-info h5\'</i>';
                break;
            case 'Medium':
                this.changeImpactBtn.innerHTML = '<i class=\'bi bi-thermometer-half ms-auto text-warning h5\'</i>';
                break;
            case 'Major':
                this.changeImpactBtn.innerHTML = '<i class=\'bi bi-thermometer-high ms-auto text-danger h5\'</i>';
                break;
        }

        this.changeImpactBtn.addEventListener('click', async () => {
            await showSwal(
                'Change Impact',
                '<p class=\'mb-2\'><span class=\'bi bi-thermometer text-info\'</span> - A Minor Change is low complexity affecting only 1 or 2 CIs. It is easy to implement and is typically done by an individual. It will not require an outage</p>' +
                '<p class=\'mb-2\'><span class=\'bi bi-thermometer-half text-warning\'</span> - A Medium Change is more complex affecting multiple CIs. It needs more expertise to perform and may require additional people to assist. It may also require an outage</p>' +
                '<p class=\'mb-2\'><span class=\'bi bi-thermometer-high text-danger\'</span> - A Major Change is the most complex affecting many CIs. It requires specialist expertise and typically requires multiple people across different teams. It will typically required an outage</p>',
                'info'
            );

        })
    }


    async drawImpactMap(depth = 2) {
        // const selected = this.cisImpacted.tomselect.getValue();
        const selected = this.cisImpacted.value  // this or the above both work
        if (selected) {
            await visNetworkClass.drawNetwork(document.getElementById('network-container'), selected, depth);
        } else {
            await visNetworkClass.destroyNetwork();
        }
    }

}

export const changeImpactClass = new ChangeImpactClass()
