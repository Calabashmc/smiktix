import {interactionDashboard} from './interaction-dashboard.js'
const newFormBtn = document.querySelector('#new-form-btn');
newFormBtn.href = '/ui/interaction/ticket/';

document.addEventListener('DOMContentLoaded', async function () {
    await interactionDashboard.init();
})