import {DynamicChart} from './dashboard-classes/dynamic-chart.js';
import {changeCalendarClass} from '/change/static/js/includes/change-calendar-class.js';


export class ChartManager {
    constructor(tabMap) {
        this.charts = {};
        this.defaultActiveTab = document.querySelector('.nav-link.active');
        this.tabMap = tabMap;
        this.tabLinks = document.querySelectorAll('[data-bs-toggle="tab"]');

        this.init();
    }

    init() {
        this.modeChange();
        this.initialLoad();
        this.setUpTabListener();
        this.detectModeChange(this.charts);
    }

    triggerDoubleClick(chartContainerId, itemName) {
        // used by filter field.
        if (this.charts[chartContainerId]) {
            this.charts[chartContainerId].simulateDoubleClick(itemName);
        } else {
            console.error(`Chart with container ID ${chartContainerId} does not exist.`);
        }
    }

    detectModeChange() {
        const body = document.querySelector('body');
        const observer = new MutationObserver(() => {
            const isDarkMode = body.classList.contains('bg-dark');
            this.updateChartColors(isDarkMode);
        });

        observer.observe(body, {attributes: true, attributeFilter: ['class']});
    }

    modeChange() {
        const isDarkMode = document.body.classList.contains('bg-dark');
        this.updateChartColors(isDarkMode);
        this.detectModeChange();
    }

    initialLoad() {
        if (this.defaultActiveTab) {
            const tabContentId = this.defaultActiveTab.getAttribute('data-bs-target');

            if (tabContentId) {
                const tabId = tabContentId.slice(1);
                this.generateChartsForActiveTab(tabId);
            }
        }
    }

    setUpTabListener() {
        this.tabLinks.forEach(tabLink => {
            tabLink.addEventListener('click', () => {
                if (tabLink.parentNode.parentNode.id.startsWith('portal')) {
                    return; // needed because using ideas tabs in portal tab form so no charts (see portal-idea-form-tab.html)
                }
                const tabContentId = tabLink.getAttribute('data-bs-target');

                if (tabContentId) {
                    const tabId = tabContentId.slice(1);

                    if (!tabId.startsWith('portal')) {
                        this.generateChartsForActiveTab(tabId);

                        // draw the change calendar.
                        if (tabId === 'cab-tab-pane') {
                            changeCalendarClass.drawEventCalendar();
                        }
                    }
                }
            });
        });
    }

    createAllCharts(tab) {
        if (!this.tabMap[tab]) return;

        for (const chartData of Object.values(this.tabMap[tab])) {
            // Always dispose existing chart first, if any
            if (this.charts[chartData.div]) {
                this.disposeChart(chartData.div);
                this.destroyCharts()
            }

            // Recreate chart
            this.charts[chartData.div] = new DynamicChart(
                chartData.api,
                chartData.div,
                chartData.chart,
                chartData.title,
                chartData.xLabel,
                chartData.scope,
                chartData.model,
                chartData.ticket_type,
                chartData.table
            );

            this.charts[chartData.div].init();
        }
    }


    destroyCharts() {
        for (const key in this.charts) {
            if (this.charts[key]) {
                const chart = this.charts[key];
                chart.dispose(); // dispose of the ECharts instance
                delete this.charts[key]; // remove it from the tracking object
            }
        }
    }


    disposeChart(chartId) {
        if (this.charts[chartId]) {
            try {
                this.charts[chartId].dispose();

                // Delete the reference
                delete this.charts[chartId];
                return true;
            } catch (error) {
                console.error(`Error disposing chart ${chartId}:`, error);
                // Still remove the reference even if there was an error
                delete this.charts[chartId];
                return false;
            }
        }
        return false;
    }

    disposeAllCharts() {
        // Fix: Use Object.keys(this.charts) instead of this.chartInstances
        Object.keys(this.charts).forEach(chartId => {
            this.disposeChart(chartId);
        });
    }

    destroy() {
        this.charts = {};
        this.tabMap = null; // Clear anything else you're holding onto
    }

    generateChartsForActiveTab(tabId) {
        const noGraphTabs = [
            'network-tab-pane',
            'team-admin-pane',
            'department-admin-pane',
            'role-admin-pane'
        ];

        if (tabId) {
            if (noGraphTabs.includes(tabId)) {
                return;
            }

            // Now create all charts for this tab
            this.createAllCharts(tabId);
        }
    }

    updateChartColors(isDarkMode) {
        Object.values(this.charts).forEach(chart => {
            if (chart && typeof chart.updateChartColors === 'function') {
                chart.updateChartColors(isDarkMode);
            }
        });
    }
}