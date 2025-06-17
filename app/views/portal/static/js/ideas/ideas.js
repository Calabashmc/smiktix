import {PortalIdeasDashboardClass} from './ideas-dashboard.js'
import {PortalIdeas} from './ideas-tab-form.js'
import {enableToolTips} from '../../../../../static/js/includes/form-classes/form-utils.js';
import {VoteClass} from '../../../../idea/static/js/vote-class.js';

window.onload = async function () {
    const portalIdeasDashboardClass = new PortalIdeasDashboardClass()
    await portalIdeasDashboardClass.init()

    const portalIdeas = new PortalIdeas();
    await portalIdeas.init()

    const voteClass = new VoteClass();
    voteClass.init();

    enableToolTips()
};