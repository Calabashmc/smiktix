class UserProfileClass {
    constructor() {
        this.assets = document.getElementById('profile-assets');
        this.department = document.getElementById('profile-department');
        this.email = document.getElementById('profile-email');
        this.firstName = document.getElementById('profile-first-name');
        this.fullName = document.getElementById('profile-full-name');
        this.lastName = document.getElementById('profile-last-name');
        this.phone = document.getElementById('profile-phone');
        this.position = document.getElementById('profile-position');
        this.profileBtn = document.getElementById('profileBtn');
        this.offcanvas = document.getElementById('profile-offcanvas');

        this.profileAvatar = document.getElementById('profile-avatar');
        this.profileModal = new bootstrap.Offcanvas(this.offcanvas);
        this.resetPasswordBtn = document.getElementById('change-passwd-btn');

        this.team = document.getElementById('profile-team');
        this.username = document.getElementById('profile-username');
    }

    init() {
        this.setupListeners();
    }

    setupListeners() {
        this.profileBtn.addEventListener('click', async () => {
            await this.getProfileData();
            this.profileModal.show();
        })

        this.resetPasswordBtn.addEventListener('click', async () => {
            const response = await fetch('/api/get_password_reset_url/')
            const data = await response.text()
            window.open(data);
        })
    }

    async getProfileData() {
        const response = await fetch('/api/get_profile_details/')
        const data = await response.json();

        if (data) {
            this.department.value = data['department'];
            this.email.value = data['email'];
            this.firstName.value = data['first_name'];
            this.fullName.value = data['full_name'];
            this.lastName.value = data['last_name'];
            this.phone.value = data['phone'];
            this.profileAvatar.src = data['avatar'];
            this.position.value = data['position'];
            this.team.value = data['my_team'];



            const myAssets = data['my_assets'];
            myAssets.forEach(asset => {
                const option = document.createElement('option');
                option.value = asset;
                option.text = asset;
                this.assets.appendChild(option);
            })
        }
    }
}

export const userProfileClass = new UserProfileClass()