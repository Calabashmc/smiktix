import {changeDashboard} from './change-dashboard.js'


document.addEventListener('DOMContentLoaded', async function () {
    const newNormalChangeFormBtn = document.getElementById('new-form-btn');
    newNormalChangeFormBtn.href = '/ui/change/ticket/normal/';

    await changeDashboard.init();
})