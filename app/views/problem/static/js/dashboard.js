import {problemDashboard} from './problem-dashboard.js'
const newFormBtn = document.querySelector('#new-form-btn');
newFormBtn.href = '/ui/problem/ticket/';

document.addEventListener('DOMContentLoaded', async function () {
    await problemDashboard.init();
})