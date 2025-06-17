import {MainDashboardClass} from './dashboard-incidents.js';

window.onload = async function () {
    const mainDashboardClass = new MainDashboardClass();
    await mainDashboardClass.init();

};
