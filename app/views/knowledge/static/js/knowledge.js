import {knowledgeClass} from './knowledge-class.js';
import {knowledgeStatus} from './knowledge-field-status.js';
import {StatusClass} from '../../../../static/js/includes/form-classes/status.js';
import {exists} from '../../../../static/js/includes/form-classes/form-utils.js';

document.addEventListener('DOMContentLoaded', async function () {
    const steps = [
        {
            id: 'new',
            label: 'New',
            icon: 'file-earmark-plus',
            allowedNext: ['internal'],
            tabs: []
        },
        {
            id: 'internal',
            label: 'Internal',
            icon: 'dice-1',
            allowedNext: ['published','reviewing', 'archived'],
            title: 'Ticket not Saved',
            message: 'The ticket must be saved before moving to the next step.',
            tabs: ['journal-tab']
        },
        {
            id: 'published',
            label: 'Published',
            icon: 'bounding-box-circles',
            allowedNext: ['internal', 'reviewing', 'archived'],
            title: 'Are you sure?',
            message: 'The Article will be viewable by all users via the Portal if Published.',
            tabs: ['journal-tab']
        },
        {
            id: 'reviewing',
            label: 'Reviewing',
            icon: 'eyeglasses',
            allowedNext: ['published', 'archived'],
            tabs: ['journal-tab']
        },
        {
            id: 'archived',
            label: 'Archived',
            icon: 'archive',
            allowedNext: [],
            message: 'This cannot be undone. The ticket will not be editable after archiving.',
            tabs: ['journal-tab',]
        },
    ]
    if (exists) {
        await knowledgeClass.init();
        await knowledgeStatus.init();
    }

    const statusClass = new StatusClass(steps);
    statusClass.init();
})