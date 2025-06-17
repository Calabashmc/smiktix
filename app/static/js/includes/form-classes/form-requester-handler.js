import {getCurrentUser} from '../utils.js';
import {tomSelectInstances} from '../tom-select.js';
import {exists} from './form-utils.js';

class RequesterHandlerClass {
    constructor() {
        this.department = document.getElementById('department');
        this.email = document.getElementById('email');
        this.exists = exists;
        this.requestedBy = document.getElementById('requested-by')
            || document.getElementById('author-id')
            || document.getElementById('owner-id');

        this.meButton = document.getElementById('requested-by-btn')
            || document.getElementById('author-id-btn')
            || document.getElementById('owner-id-btn');

        this.occupation = document.getElementById('occupation');
        this.phone = document.getElementById('phone');
    }

    async init() {
        await this.setRequesterDetailsOnLoad()
        await this.setUpListeners();
    }

    async setUpListeners() {
        this.meButton.addEventListener('click', async () => {
            await this.handleMeButton();
        });

        this.requestedBy.addEventListener('change', async () => {
            await this.fetchUserDetails();
        });
    }

    async setRequesterDetailsOnLoad() {
        if (this.exists) {
            await this.fetchUserDetails()
        }
    }

    async handleMeButton() {
        this.tomSelect = await tomSelectInstances.get(this.requestedBy.id);
        const currentUser = await getCurrentUser();
        this.requestedBy.value = currentUser['user_id'];
        // Set value using the TomSelect instance
        if (this.tomSelect) {
            this.tomSelect.setValue([currentUser['user_id']]);
        }

        await this.fetchUserDetails();
    }

    async fetchUserDetails() {
        // Fetch user details and update the DOM
        try {
            const id = this.requestedBy.value;
            const response = await fetch(`/api/people/get_requester_details/?id=${id}`);
            const userData = await response.json();
            // Only update DOM elements if the data has changed
            if (userData) {
                this.occupation.value = ` ${userData['user_occupation'] ?? 'Occupation unknown'}`;
                this.department.value = ` ${userData['user_department'] ?? 'Department unknown'}`;
                this.email.value = ` ${userData['user_email'] ?? 'Email unknown'}`;
                this.phone.value = ` ${userData['user_phone'] ?? 'Phone unknown'}`;
            }
        } catch (error) {
            console.log(error)
        }
    }
}

export const requesterHandler = new RequesterHandlerClass();
