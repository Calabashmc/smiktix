import {cmdbDashboard} from "./cmdb-dashboard.js"
import {formButtonHandlers} from "../../../../static/js/includes/form-classes/form-button-handlers.js";

document.addEventListener('DOMContentLoaded', async function () {
    await cmdbDashboard.init();

    const newCIBtn = document.getElementById("new-form-btn");
    newCIBtn.addEventListener("click", async () => {
        await formButtonHandlers.handleNewFormBtn();
    })

})