import {getCurrentUser} from './utils.js';
import {showSwal} from './form-classes/form-utils.js';

export class UserAvatarClass {
    constructor() {
        this.avatar = document.getElementById('avatar');

        this.selectedAvatar = document.getElementById('selected-avatar');
        this.modal = document.getElementById('set-avatar-modal');
        this.setAvatarModal = new bootstrap.Modal(this.modal);

        this.setAvatarModalSaveBtn = document.getElementById('modal-set-icon-btn');
        this.setAvatarModalCancelBtn = document.getElementById('modal-cancel-btn');

        // avatar image in profile offcanvas and add user offcanvas.
        this.profileHeaderAvatar = document.getElementById('header-user-avatar'); // avatar in profile in header
        this.userAvatar = document.getElementById('user-avatar'); // avatar in admin user form
        this.profileAvatar = document.getElementById('profile-avatar'); // in profile off-canvas


        // offcanvas's to remove focus from to avoid Blocked aria-hidden warnings
        this.profileFlag = false;  // flag to check if profile avatar (if true) or user avatar (if false)
        this.profileOffcanvas = document.getElementById('profile-offcanvas');
        this.addUserOffcanvas = document.getElementById('add-user-offcanvas');

        this.userId = document.getElementById('user-id');
        this.userIdValue = null;
    }

    init() {
        this.setupListeners();
    };

    setupListeners() {
        this.profileAvatar.addEventListener('dblclick', async () => {
            this.selectedAvatar.src = this.profileAvatar.src;
            this.avatar.addEventListener('change', () => {
                this.selectedAvatar.src = this.avatar.options[this.avatar.selectedIndex].value;
            })

            const currentUser = await getCurrentUser();
            this.userIdValue = currentUser['user_id'];  // overwrite user id with current user for profile avatar
            this.profileFlag = true; // set flag to profile avatar
            this.setAvatarModal.show()
        });

        this.userAvatar?.addEventListener('dblclick', () => {
            this.selectedAvatar.src = this.userAvatar.src;
            this.avatar.addEventListener('change', () => {
                this.selectedAvatar.src = this.avatar.options[this.avatar.selectedIndex].value;
            })
            this.profileFlag = false; // set flag to user avatar
            this.userIdValue = this.userId.value;
            this.setAvatarModal.show()
        });

        this.setAvatarModalSaveBtn.addEventListener('click', async () => {
            await this.handleSetAvatar();
        })

        this.setAvatarModalCancelBtn.addEventListener('click', () => {
            this.setAvatarModal.hide();
        });

    }

    async handleSetAvatar() {
        this.setAvatarModal.hide();

        if (this.userAvatar) {
            this.userAvatar.src = this.selectedAvatar.src
        }

        if (this.profileFlag === true) {
            this.profileAvatar.src = this.selectedAvatar.src;
            this.profileHeaderAvatar.src = this.selectedAvatar.src;
        } else {
            this.userAvatar.src = this.selectedAvatar.src;
        }

        const apiArgs = {
            'user-id': this.userIdValue,
            'avatar': this.selectedAvatar.src
        }

        const response = await fetch('/api/people/update-avatar/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(apiArgs)
        });

        const data = await response.json();

        if (!response.ok) {
            console.error('Error:', data['error']);
            await showSwal('Error', data.error || 'Avatar could not be set', 'error');
        }
    }

    addInert() {
        this.modal.removeAttribute('aria-hidden');
        this.addUserOffcanvas?.setAttribute('inert', '');
        this.profileOffcanvas?.setAttribute('inert', '');
    }

    removeInert() {
        this.modal.setAttribute('aria-hidden', 'true');
        this.profileOffcanvas?.removeAttribute('inert');
        this.addUserOffcanvas?.removeAttribute('inert');
    }
}
