import {cmdbClass} from './cmdb-class.js';
import {StatusClass} from '../../../../static/js/includes/form-classes/status.js';

document.addEventListener('DOMContentLoaded', async function () {
    const ticketType = document.getElementById('ticket-type').value;

    // Service has a compliance tab Hardware and Software don't
    const getTabs = (ticketType) => {
        const baseTabs = ['journal-tab', 'cmdb-lifecycle-tab', 'cmdb-operational-tab', 'relationship-tab', 'cmdb-vendor-tab'];
        return ticketType === 'Service' ? [...baseTabs, 'compliance-tab'] : baseTabs;
    };

    const getSteps = (ticketType) => [
        {
            id: 'new',
            label: 'New',
            icon: 'file-earmark-plus',
            allowedNext: ['configuring'],
            tabs: []
        },
        {
            id: 'configuring',
            label: 'Configuring',
            icon: 'pencil-square',
            allowedNext: ['testing'],
            title: 'Ticket not Saved',
            message: 'The ticket must be saved before moving to the next step.',
            tabs: getTabs(ticketType)
        },
        {
            id: 'testing',
            label: 'Testing',
            icon: 'pencil-square',
            allowedNext: ['operational'],
            tabs: getTabs(ticketType)
        },
        {
            id: 'operational',
            label: 'Operational',
            icon: 'tools',
            allowedNext: ['testing', 'retired'],
            tabs: getTabs(ticketType)
        },
        {
            id: 'retired',
            label: 'Retired',
            icon: 'box2',
            allowedNext: ['operational', 'build', 'implement', 'review'],
            tabs: getTabs(ticketType)
        },
        {
            id: 'disposed',
            label: 'Disposed',
            icon: 'recycle',
            allowedNext: [],
            tabs: getTabs(ticketType)
        },
    ];


    await cmdbClass.init()

    // Initialize the stepper
    const steps = getSteps(ticketType);
    const statusClass = new StatusClass(steps);
    statusClass.init();
    // Make statusClass global, so I can reference within resolution-class to call goToPriorStep
    window.statusClass = statusClass;
})