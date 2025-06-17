import {slaConfigClass} from "./sla-config.js";
import {lookupTablesClass} from "./lookup-tables.js";
import {appDefaults} from "./set-app-defaults.js";

document.addEventListener('DOMContentLoaded', async function () {
    await slaConfigClass.init();
    await lookupTablesClass.init()
    appDefaults.init();
})

