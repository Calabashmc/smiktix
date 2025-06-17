import {DateTime} from '../../../../../static/js/luxon/luxon.min.js';

class ChangeCalendarClass {
    constructor() {
        this.data = [];
        this.items = [];
        this.resources = []
    }

    async getResources() {
        const response = await fetch('/api/change/get-change-resources/')
        const data = await response.json();

        if (!response.ok) {
            await showSwal('Error', `Unable to fetch resources ${data.error}`, 'error');
        }
        this.resources = data
    }

    async drawEventCalendar() {
        await this.getResources();

        const response = await fetch('/api/change/changes-scheduled/')
        const data = await response.json();

        if (!response.ok) {
            await showSwal('Error', `Unable to fetch scheduled changes ${data.error}`, 'error');
        }
        const schedules = data.map(change => ({
            id: change.id,
            title: change.content,
            allDay: false,
            start: DateTime.fromISO(change.start).toISO(),
            end: DateTime.fromISO(change.end).toISO(),
            resourceId: change.resourceId,
            display: 'auto',
            className: change.className,
        }));

        let clickTimer = null;

        let ec = new EventCalendar(document.getElementById('event-calendar'), {
            view: 'timeGridWeek',
            headerToolbar: {
                start: 'prev,next today',
                center: 'title',
                end: 'dayGridMonth,timeGridWeek,timeGridDay,listMonth resourceTimeGridWeek,resourceTimelineMonth'
            },
            resources: this.resources,
            scrollTime: '09:00:00',
            events: schedules,
            views: {
                timeGridWeek: {pointer: true},
                resourceTimeGridWeek: {pointer: true},
                resourceTimelineWeek: {
                    pointer: true,
                    slotMinTime: '00:00',
                    slotMaxTime: '23:59',
                    slotWidth: 80,
                    resources: this.resources
                }
            },
            dayMaxEvents: false,
            nowIndicator: true,
            selectable: true,
            eventClick: function (info) {
                if (clickTimer) {
                    clearTimeout(clickTimer); // Cancel the single-click action
                    clickTimer = null;
                    // event.title has within it Type: <type>, so use regex to extract
                    const changeType = info.event.title.match(/Type:\s*(\w+)/)[1].toLowerCase();

                    window.open(`/ui/change/ticket/${changeType}/?ticket=${info.event.id}`, '_blank');
                } else {
                    clickTimer = setTimeout(() => {
                        console.log('Single click detected on event:', info.event.title);
                        clickTimer = null;
                    }, 300); // Adjust delay to detect double-clicks (300ms is typical)
                }
            }
        });
    }

}

export const changeCalendarClass = new ChangeCalendarClass()