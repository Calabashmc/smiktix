import {releaseDashboard} from './release-dashboard.js'
const newFormBtn = document.querySelector('#new-form-btn');
newFormBtn.href = '/ui/release/ticket/';

document.addEventListener('DOMContentLoaded', async function () {
    await releaseDashboard.init();
})