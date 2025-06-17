import {ParentClass} from './includes/parent-class.js';
import {outageClass} from './includes/outage-class.js';
import {priorityButtonsClass} from './includes/interaction-priority-button-class.js';
import {slaClass} from './includes/sla-class.js';
import {ChildrenClass} from '../../../../static/js/includes/children-class.js';
import {interactionFormClass} from './interaction-form.js';
import {StatusClass} from '../../../../static/js/includes/form-classes/status.js';
import {exists} from '../../../../static/js/includes/form-classes/form-utils.js';
import {InteractionFieldStatusClass} from './includes/interaction-field-status.js';


// All DOM elements for the Interaction form cached globally here
document.addEventListener('DOMContentLoaded', async function () {
    const steps = [
        {
            id: 'new',
            label: 'New',
            icon: 'file-earmark-plus',
            allowedNext: ['in-progress'],
            tabs: []
        },
        {
            id: 'in-progress',
            label: 'In Progress',
            icon: 'pencil-square',
            allowedNext: ['resolved'],
            title: 'Ticket not Saved',
            message: 'The ticket must be saved before moving to the next step.',
            tabs: ['journal-tab']
        },
        {
            id: 'resolved',
            label: 'Resolved',
            icon: 'tools',
            allowedNext: ['in-progress', 'review', 'closed'],
            tabs: ['journal-tab', 'resolution-tab']
        },
        {
            id: 'review',
            label: 'Review',
            icon: 'bootstrap-reboot',
            allowedNext: ['closed'],
            tabs: ['journal-tab', 'resolution-tab', 'incident-review-tab']
        },
        {
            id: 'closed', label: 'Closed', icon: 'archive-fill', allowedNext: [],
            title: 'Are you sure?',
            message: 'This cannot be undone. The ticket will not be editable after closing.',
            tabs: ['journal-tab', 'resolution-tab', 'incident-review-tab']
        },
    ];

    if (exists) {
        const parentClass = new ParentClass();
        parentClass.init();

        const childColumns = [
            {
                title: 'Ticket #',
                headerHozAlign: 'center',
                field: 'ticket_number',
                hozAlign: 'center',
            },
            {
                title: 'Type',
                headerHozAlign: 'center',
                field: 'ticket_type',
                hozAlign: 'center',

            },
            {
                title: 'Priority',
                headerHozAlign: 'center',
                field: 'priority',
                hozAlign: 'center',
                width: 100
            },
            {
                title: 'Status',
                headerHozAlign: 'center',
                field: 'status',
                hozAlign: 'center',
            },
            {
                title: 'Support Team',
                field: 'support_team',
                width: 300
            },
            {
                title: 'Short Description',
                field: 'shortDesc',
                width: 300
            },
        ]
        //
        // const childrenTab = document.querySelector('#children-tab')
        // childrenTab.classList.remove('disabled')

        const childrenClass = new ChildrenClass(childColumns);
        childrenClass.init()
        window.childrenClass = childrenClass

        slaClass.init();
    }

    priorityButtonsClass.init();
    outageClass.init();
    interactionFormClass.init();

    // StatusClass is initialised here as it needs steps passed to it
    // each model has a different set of steps based on the form
    const statusClass = new StatusClass(steps);
    statusClass.init();
    // Make statusClass global, so I can reference within resolution-class to call goToPriorStep
    window.statusClass = statusClass;

    const interactionFieldStatusClass = new InteractionFieldStatusClass();
    interactionFieldStatusClass.init();

    //     disable changing the ticket creator
    const createdBy = document.getElementById('created-by');
    createdBy.addEventListener('mousedown', (e) => {
        e.preventDefault();
    });
    createdBy.addEventListener('keydown', (e) => {
        e.preventDefault();
    })

})
