import {PortalKbaDashboardClass} from './knowledge-dashboard.js'
import {KnowledgeOffcanvasFormClass} from './knowledge-offcanvas-form.js'
import {enableToolTips} from '../../../../../static/js/includes/form-classes/form-utils.js';

window.onload = async function () {
    const portalKbaDashboardClass = new PortalKbaDashboardClass();
    await portalKbaDashboardClass.init()
    window.portalKbaDashboardClass = portalKbaDashboardClass

    const knowledgeOffCanvasForm = new KnowledgeOffcanvasFormClass();
    knowledgeOffCanvasForm.init();

    window.knowledgeOffCanvasForm = knowledgeOffCanvasForm;
    enableToolTips()
};