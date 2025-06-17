// THis class is used to build the full name field from first and last name
// it is used in the user profile page and in the registration form
class FullnameClass {
    constructor() {
        this.first_name = document.getElementById('first_name');
        this.last_name = document.getElementById('last_name');
        this.full_name = document.getElementById('full_name');
        this.first_name = document.querySelector('#first_name input');
        this.last_name = document.querySelector('#last_name input');
        this.full_name = document.querySelector('#full_name input');
    }

    init() {
        this.setupListeners()
    }

    setupListeners() {
        this.first_name.addEventListener('input', () => {
            this.full_name.value = this.first_name.value + ' ' + this.last_name.value
        })

        this.last_name.addEventListener('input', () => {
            this.full_name.value = this.first_name.value + ' ' + this.last_name.value;
        })
    }
}

document.addEventListener('DOMContentLoaded', () => {
    const fullnameClass = new FullnameClass();
    fullnameClass.init();
});