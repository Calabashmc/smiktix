import {InteractionDashboard} from "./my-tickets-dashboard.js"
import {PortalMyTickets} from "./my-tickets-tab-form.js";

window.onload = async function () {
    const interactionDashboardClass = new InteractionDashboard()
    await interactionDashboardClass.init()

    const myTickets = new PortalMyTickets()
    await myTickets.init()

    const urlParams = new URLSearchParams(window.location.search);
    const activeTab = urlParams.get("active_tab");

    if (activeTab === "support") {
        const supportTab = document.getElementById("portal-interactions-tab");
        if (supportTab) {
            const tab = new bootstrap.Tab(supportTab);
            tab.show();
        }
    }
};