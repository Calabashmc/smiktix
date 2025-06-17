import {VoteClass} from "./vote-class.js";
import {ideaConsiderationsClass} from "./idea-considerations.js";
import {ideaFieldStatus} from "./idea-field-status.js";
import {StatusClass} from '../../../../static/js/includes/form-classes/status.js';

document.addEventListener('DOMContentLoaded', async function () {
    const steps = [
        {
            id: 'new',
            label: 'New',
            icon: 'file-earmark-plus',
            allowedNext: ['ideation'],
            tabs:[]
        },
        {
            id: 'ideation',
            label: 'Ideation',
            icon: 'pencil-square',
            allowedNext: ['voting'],
            title: 'Ticket not Saved',
            message: 'The ticket must be saved before moving to the next step.',
            tabs: ['journal-tab', 'benefit-impact-tab', 'considerations-tab']
        },
        {
            id: 'voting',
            label: 'Voting',
            icon: 'tools',
            allowedNext: ['adopt'],
            tabs: ['journal-tab', 'benefit-impact-tab', 'considerations-tab']
        },
        {
            id: 'adopt',
            label: 'Adopt',
            icon: 'list-check',
            allowedNext: ['pdca', 'review'],
            title: 'Voting not complete',
            message: 'The Idea is still being voted on',
            tabs: ['journal-tab', 'benefit-impact-tab', 'considerations-tab']
        },
        {
            id: 'pdca',
            label: 'PDCA',
            icon: 'bootstrap-reboot',
            allowedNext: ['review'],
            title: 'Idea Rejected',
            message: 'The Idea is not being considered for implementation at this stage',
            tabs: ['journal-tab', 'benefit-impact-tab', 'considerations-tab']
        },
        {
            id: 'review',
            label: 'Review',
            icon: 'card-checklist',
            allowedNext: ['closed'],
            tabs: ['journal-tab', 'benefit-impact-tab', 'considerations-tab', 'resolution-tab']
        },
        {
            id: 'closed',
            label: 'Close',
            icon: 'archive-fill',
            allowedNext: [],
            tabs: ['journal-tab', 'benefit-impact-tab', 'considerations-tab', 'resolution-tab']
        }
    ];

    const voteClass = new VoteClass();
    voteClass.init();

    ideaConsiderationsClass.init();
    await ideaFieldStatus.init();

    // Initialize the stepper
    const statusClass = new StatusClass(steps);
    statusClass.init();
    // Make statusClass global, so I can reference within resolution-class to call goToPriorStep
    window.statusClass = statusClass;
})