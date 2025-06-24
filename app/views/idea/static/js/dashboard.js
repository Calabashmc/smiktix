import {ideasDashboard} from './ideas-dashboard.js'
const newFormBtn = document.querySelector('#new-form-btn');
newFormBtn.href = '/ui/idea/ticket/';

document.addEventListener('DOMContentLoaded', async function () {
    const ideaTableDiv = document.querySelector('#all-ideas-table')
    await ideasDashboard.init();
})