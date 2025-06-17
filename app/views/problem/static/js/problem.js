import {AnalysisMethodClass} from "./includes/analysis-method-class.js";
import {priorityButtonsClass} from "./includes/problem-priority-button-class.js";
import {problemDashboard} from "./problem-dashboard.js";
import {ChildrenClass} from "../../../../static/js/includes/children-class.js";
import {StatusClass} from '../../../../static/js/includes/form-classes/status.js';
import {exists} from "../../../../static/js/includes/form-classes/form-utils.js";

document.addEventListener('DOMContentLoaded', async function () {
    const isParent = true; // Problem tickets are always parents. Set this so

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
            allowedNext: ['analysis'],
            title: 'Ticket not Saved',
            message: 'The ticket must be saved before moving to the next step.',
            tabs: ['journal-tab', 'children-tab']
        },
        {
            id: 'analysis',
            label: 'Analysis',
            icon: 'binoculars',
            allowedNext: ['resolved'],
            tabs: ['journal-tab', 'children-tab', 'analysis-tab']
        },
        {
            id: 'resolved',
            label: 'Resolved',
            icon: 'tools',
            allowedNext: ['testing', 'closed'],
            tabs: ['journal-tab', 'children-tab', 'analysis-tab', 'resolution-tab']
        },
        {
            id: 'closed',
            label: 'Closed',
            icon: 'archive-fill',
            allowedNext: [],
            title: 'Are you sure?',
            message: 'This cannot be undone. The ticket will not be editable after closing.',
            tabs: ['journal-tab', 'children-tab', 'analysis-tab', 'resolution-tab']
        },
    ];


    if (exists) {
        const childrenTab = document.querySelector("#children-tab")
        childrenTab.classList.remove("disabled")
        const childrenClass = new ChildrenClass(await problemDashboard.getProblemColumns());
        await childrenClass.init()
        window.childrenClass = childrenClass

        const analysisMethodClass = new AnalysisMethodClass();
        analysisMethodClass.init();
    }

    priorityButtonsClass.init();

    const statusClass = new StatusClass(steps);
    statusClass.init();
    // Make statusClass global, so I can reference within resolution-class to call goToPriorStep
    window.statusClass = statusClass;

})

