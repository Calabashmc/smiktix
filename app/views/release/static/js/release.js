import {StatusClass} from '../../../../static/js/includes/form-classes/status.js';
import {ReleaseFormClass} from './release-form.js';

document.addEventListener('DOMContentLoaded', async function () {

    const steps = [
        {
            id: 'new',
            label: 'New',
            icon: 'file-earmark-plus',
            allowedNext: ['build'],
            tabs: []
        },
        {
            id: 'build',
            label: 'Build',
            icon: 'tools',
            allowedNext: ['test'],
            title: 'Ticket not Saved',
            message: 'The ticket must be saved before moving to the next step.',
            tabs: ['journal-tab', 'release-build-tab']
        },
        {
            id: 'test',
            label: 'Stage/Test',
            icon: 'list-check',
            allowedNext: ['build', 'approval'],
            tabs: ['journal-tab', 'release-build-tab', 'release-test-tab']
        },
        {
            id: 'approval',
            label: 'Approval',
            icon: 'person-check',
            allowedNext: ['test', 'release', 'deploy'],
            title: 'Testing Not Complete',
            message: 'Testing needs to be confirmed as successful in the test tab before moving to the next step.',
            tabs: ['journal-tab', 'release-build-tab', 'release-test-tab', 'release-approval-tab']
        },
        {
            id: 'release',
            label: 'Release',
            icon: 'hdd-stack',
            allowedNext: ['deploy'],
            title: 'Not Ready for Release',
            message: 'The Release has not been marked as approved',
            tabs: ['journal-tab', 'release-build-tab', 'release-test-tab', 'release-approval-tab', 'release-release-tab']
        },
        {
            id: 'deploy',
            label: 'Deploy',
            icon: 'rocket-takeoff',
            allowedNext: ['release', 'review'],
            title: 'Not Ready for Deployment',
            message: 'The Release has not been marked as "Build successful"',
            tabs: ['journal-tab', 'release-build-tab', 'release-test-tab', 'release-approval-tab', 'release-release-tab', 'release-deploy-tab']
        },
        {
            id: 'review',
            label: 'Review',
            icon: 'card-checklist',
            allowedNext: ['closed'],
            tabs: ['journal-tab', 'release-build-tab','release-test-tab', 'release-approval-tab', 'release-release-tab', 'release-deploy-tab', 'release-review-tab']
        },
        {
            id: 'closed',
            label: 'Close',
            icon: 'archive-fill',
            allowedNext: [],
            tabs: ['journal-tab', 'release-test-tab', 'release-approval-tab', 'release-release-tab', 'release-deploy-tab', 'release-review-tab']
        }
    ];

    // Initialize the stepper
    const statusClass = new StatusClass(steps);
    statusClass.init();
    // Make statusClass global, so I can reference within resolution-class to call goToPriorStep
    window.statusClass = statusClass;

    const releaseFormClass = new ReleaseFormClass();
    await releaseFormClass.init();
});
