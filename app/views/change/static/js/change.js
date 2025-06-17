import {ChangeCabClass} from './change-cab.js';
import {ChildrenClass} from '../../../../static/js/includes/children-class.js';
import {changeImpactClass} from './change-impact-class.js';
import {changeApprovalsClass} from './change-approvals.js';
import {ChangeWindowClass} from './change-window.js';
import {ChangeRiskClass} from './change-risk.js';
import {changeRiskButtonsClass} from './includes/change-risk-buttons-class.js';
import {exists} from '../../../../static/js/includes/form-classes/form-utils.js';
import {problemDashboard} from '../../../problem/static/js/problem-dashboard.js';
import {StatusClass} from '../../../../static/js/includes/form-classes/status.js';
import {StandardChangeClass} from './includes/standard-change.js';
import {ChangeResolutionClass} from './includes/change-resolution-class.js';
import {ChangeFieldStatusClass} from './includes/change-field-status.js';

document.addEventListener('DOMContentLoaded', async function () {
    const changeType = document.getElementById('change-type');
    let steps = []

    if (changeType.value === 'Normal') {
        steps = [
            {
                id: 'new',
                label: 'New',
                icon: 'file-earmark-plus',
                allowedNext: ['plan'],
                tabs: []
            },
            {
                id: 'plan',
                label: 'Plan',
                icon: 'pencil-square',
                allowedNext: ['build'],
                title: 'Ticket not Saved',
                message: 'The ticket must be saved before moving to the next step.',
                tabs: ['journal-tab', 'children-tab', 'change-plans-tab']
            },
            {
                id: 'build',
                label: 'Build/Test',
                icon: 'tools',
                allowedNext: ['plan', 'approval'],
                tabs: ['journal-tab', 'children-tab', 'change-plans-tab', 'change-test-tab']
            },
            {
                id: 'approval',
                label: 'Approval',
                icon: 'person-check',
                allowedNext: ['plan', 'build', 'cab',],
                title: 'Testing Not Complete',
                message: 'Testing needs to be confirmed as successful in the test tab before moving to the next step.',
                tabs: ['journal-tab', 'children-tab', 'change-plans-tab', 'change-test-tab', 'change-approvals-tab']
            },
            {
                id: 'cab',
                label: 'CAB',
                icon: 'taxi-front-fill',
                allowedNext: ['implement', 'review', 'closed'],
                title: 'Not Ready for CAB',
                message: 'The Change has not been marked as Ready for CAB.',
                tabs: ['journal-tab', 'children-tab', 'change-plans-tab', 'change-test-tab', 'change-approvals-tab', 'cab-tab'],
            },
            {
                id: 'implement',
                label: 'Implement',
                icon: 'rocket-takeoff',
                allowedNext: ['review', 'closed'],
                tabs: ['journal-tab', 'children-tab', 'change-plans-tab', 'change-test-tab', 'change-approvals-tab', 'cab-tab', 'resolution-tab'],
            },
            {
                id: 'review',
                label: 'Review',
                icon: 'bootstrap-reboot',
                allowedNext: ['closed'],
                tabs: ['journal-tab', 'children-tab', 'change-plans-tab', 'change-test-tab', 'change-approvals-tab', 'cab-tab', 'resolution-tab', 'change-review-tab'],
            },
            {
                id: 'closed',
                label: 'Closed',
                icon: 'archive-fill',
                allowedNext: [],
                title: 'Are you sure?',
                message: 'This cannot be undone. The ticket will not be editable after closing.',
                tabs: ['journal-tab', 'children-tab', 'change-plans-tab', 'change-test-tab', 'change-approvals-tab', 'cab-tab', 'resolution-tab', 'change-review-tab'],
            }
        ];
        if (exists) {
            const childrenTab = document.getElementById('children-tab')
            childrenTab.classList.remove('disabled')

            const childrenClass = new ChildrenClass(await problemDashboard.getProblemColumns());
            childrenClass.init()
            window.childrenClass = childrenClass
        }

        changeApprovalsClass.init();

        const changeRiskClass = new ChangeRiskClass();
        changeRiskClass.init();

        const changeCabClass = new ChangeCabClass();
        changeCabClass.init();

        const changeWindowClass = new ChangeWindowClass();
        changeWindowClass.init();

    } else if (changeType.value === 'Standard') {
        steps = [
            {
                id: 'new',
                label: 'New',
                icon: 'file-earmark-plus',
                allowedNext: ['plan'],
                tabs: []
            },
            {
                id: 'plan',
                label: 'Plan',
                icon: 'pencil-square',
                allowedNext: ['build'],
                title: 'Ticket not Saved',
                message: 'The ticket must be saved before moving to the next step.',
                tabs: ['journal-tab']
            },
            {
                id: 'implement',
                label: 'Implement',
                icon: 'rocket-takeoff',
                allowedNext: ['review', 'closed'],
                tabs: ['journal-tab', 'resolution-tab'],
            },
            {
                id: 'review',
                label: 'Review',
                icon: 'bootstrap-reboot',
                allowedNext: ['closed'],
                tabs: ['journal-tab', 'resolution-tab', 'change-review-tab'],
            },
            {
                id: 'closed',
                label: 'Closed',
                icon: 'archive-fill',
                allowedNext: [],
                title: 'Are you sure?',
                message: 'This cannot be undone. The ticket will not be editable after closing.',
                tabs: ['journal-tab', 'resolution-tab', 'change-review-tab'],
            }
        ];

        const standardChangeClass = new StandardChangeClass();
        standardChangeClass.init();

    } else {
        steps = [
            {
                id: 'new',
                label: 'New',
                icon: 'file-earmark-plus',
                allowedNext: ['plan'],
                tabs: []
            },
            {
                id: 'plan',
                label: 'Plan',
                icon: 'pencil-square',
                allowedNext: ['implement'],
                title: 'Ticket not Saved',
                message: 'The ticket must be saved before moving to the next step.',
                tabs: ['journal-tab']
            },
            {
                id: 'implement',
                label: 'Implement',
                icon: 'rocket-takeoff',
                allowedNext: ['review'],
                title: 'eCAB Approval Required',
                message: 'The Emergency CAB needs to be approved before implementing',
                tabs: ['journal-tab', 'resolution-tab'],
            },
            {
                id: 'review',
                label: 'Review',
                icon: 'bootstrap-reboot',
                allowedNext: ['closed'],
                tabs: ['journal-tab', 'resolution-tab', 'change-review-tab'],
            },
            {
                id: 'closed',
                label: 'Closed',
                icon: 'archive-fill',
                allowedNext: [],
                title: 'Are you sure?',
                message: 'This cannot be undone. The ticket will not be editable after closing.',
                tabs: ['journal-tab', 'resolution-tab', 'change-review-tab'],
            }
        ];
    }

    changeImpactClass.init();
    changeRiskButtonsClass.init();

    const statusClass = new StatusClass(steps);
    statusClass.init();

    const changeResolutionClass = new ChangeResolutionClass();
    changeResolutionClass.init();

    const changeFieldStatusClass = new ChangeFieldStatusClass();
    changeFieldStatusClass.init();
})