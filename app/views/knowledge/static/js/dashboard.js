import {knowledgeDashboard} from './knowledge-dashboard.js'
const newFormBtn = document.querySelector('#new-form-btn');
newFormBtn.href = '/ui/knowledge/ticket/';

document.addEventListener('DOMContentLoaded', async function () {
    await knowledgeDashboard.init();
})