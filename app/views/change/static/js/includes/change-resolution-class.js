import {showFormButtons} from '../../../../../static/js/includes/form-classes/form-utils.js';

export class ChangeResolutionClass {
    constructor() {
        this.changeJoy = document.getElementById('change-joy');
        this.changeSuccessRadio = document.getElementById('change-successful');
        this.failReasons = document.getElementById('fail-reasons');

    }

    init() {
        this.setupListeners();
        this.setFailReasonsDivDisplay();
    }

    setupListeners() {
        this.changeSuccessRadio.addEventListener('change', () => {
            if (this.changeSuccessRadio.checked) {
                this.failReasons.classList.add('d-none')
                this.changeJoy.src = '/change/static/images/happy-change.svg';
                showFormButtons()
            } else {
                this.failReasons.classList.remove('d-none')
                this.changeJoy.src = '/change/static/images/sad-change.svg';
                showFormButtons()
            }
        })
    }

    setFailReasonsDivDisplay() {
        if (this.changeSuccessRadio.checked) {
            this.failReasons.classList.add('d-none');
            this.changeJoy.src = '/change/static/images/happy-change.svg';
        } else {
            this.failReasons.classList.remove('d-none');
            this.changeJoy.src = '/change/static/images/sad-change.svg';
        }
    }
}