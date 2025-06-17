import {DateTime} from '../../../../static/js/luxon/luxon.min.js';
import {showFormButtons, showSwal} from '../../../../static/js/includes/form-classes/form-utils.js';
import {setSliderInitial} from '../../../../static/js/includes/utils.js';

export class ChangeWindowClass {
    // Constants
    static WEEKDAYS = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
    static SLIDER_COLORS = {
        DURATION: '#0414f4',
        DOWNTIME: '#ff0000'
    };
    static LEAD_TIME_WARNING_THRESHOLD = '5';

    constructor() {
        // Button elements
        this.changeInHoursBtn = this.getElementById('in-hours-btn');
        this.changeInHoursBtnLabel = document.querySelector('label[for="in-hours-btn"]');
        this.changeOutOfHoursBtn = this.getElementById('after-hours-btn');
        this.changeChangeWindowBtn = this.getElementById('change-window-btn');

        // Modal elements
        this.changeWindowModal = new bootstrap.Modal(this.getElementById('change-window-modal'));
        this.modalOKBtn = this.getElementById('modal-ok-btn');
        this.modalCancelBtn = this.getElementById('modal-cancel-btn');

        // Form elements
        this.changeWindows = this.getElementById('change-windows');
        this.changeWindowDate = this.getElementById('change-window-date');
        this.changeWindowLeadTimeRadio = document.querySelectorAll('input[name="change-window-radio"]');

        // Slider elements
        this.downtimeLabel = this.getElementById('downtime-slider-label');
        this.downtimeSlider = this.getElementById('change-downtime');
        this.durationLabel = this.getElementById('duration-slider-label');
        this.durationSlider = this.getElementById('change-duration');

        // Date/time elements
        this.startDate = this.getElementById('start-date');
        this.startTime = this.getElementById('start-time');
        this.endDate = this.getElementById('end-date');
        this.endTime = this.getElementById('end-time');
    }

    getElementById(id) {
        const element = document.getElementById(id);
        if (!element) {
            console.warn(`Element with ID '${id}' not found`);
        }
        return element;
    }

    async init() {
        try {
            this.initializeState();
            await this.getBusinessHours();
            this.initializeSliders();
            this.disableChangeLeadtimeRadioButtons();
            this.setupEventListeners();
        } catch (error) {
            console.error('Failed to initialize ChangeWindowClass:', error);
        }
    }

    initializeState() {
        this.leadtime = 1;
        this.officeStartTime = null;
        this.officeEndTime = null;
        this.changeDate = null;
    }

    async getBusinessHours() {
        try {
            const response = await fetch('/api/get_business_hours/');
            const data = await response.json();

            if (!response.ok) {
                await showSwal('Error', `Unable to fetch business hours ${data.error}`, 'error');
            }

            this.officeStartTime = data.start;
            this.officeEndTime = data.end;

        } catch (error) {
            console.error('Failed to fetch business hours:', error);
            throw error;
        }
    }

    getTodaysDate() {
        return DateTime.local().toISODate();
    }

    async displayDateInModal() {
        try {
            this.changeDate = await this.getDateForDay(this.changeWindows.value, Number(this.leadtime));

            if (this.changeWindowDate) {
                this.changeWindowDate.innerHTML = this.changeDate;
            }
        } catch (error) {
            console.error('Failed to display date in modal:', error);
        }
    }

    setupEventListeners() {
        this.setupButtonListeners();
        this.setupModalListeners();
        this.setupFormListeners();
        this.setupSliderListeners();
    }

    setupButtonListeners() {
        this.changeInHoursBtn?.addEventListener('click', async () => {
            try {
                await this.handleInHoursClick();
            } catch (error) {
                console.error('Error handling in-hours click:', error);
            }
        });

        this.changeOutOfHoursBtn?.addEventListener('click', async () => {
            try {
                await this.handleOutOfHoursClick();
            } catch (error) {
                console.error('Error handling out-of-hours click:', error);
            }
        });

        this.changeChangeWindowBtn?.addEventListener('click', () => {
            this.changeWindowModal?.show();
        });
    }

    async handleInHoursClick() {
        const todaysDate = this.getTodaysDate();
        this.setFormValues({
            startTime: this.officeStartTime,
            endTime: this.officeEndTime,
            startDate: todaysDate,
            endDate: todaysDate
        });
        showFormButtons();
    }

    async handleOutOfHoursClick() {
        const todaysDate = this.getTodaysDate();
        const tomorrowsDate = DateTime.local().plus({days: 1}).toISODate();

        this.setFormValues({
            startTime: this.officeEndTime,
            endTime: this.officeStartTime,
            startDate: todaysDate,
            endDate: tomorrowsDate
        });
        showFormButtons();
    }

    setFormValues({startTime, endTime, startDate, endDate}) {
        if (this.startTime) this.startTime.value = startTime;
        if (this.endTime) this.endTime.value = endTime;
        if (this.startDate) this.startDate.value = startDate;
        if (this.endDate) this.endDate.value = endDate;
    }

    setupModalListeners() {
        this.modalOKBtn?.addEventListener('click', async() => {
            try {
                await this.handleModalOK();
            } catch (error) {
                console.error('Error handling modal OK:', error);
            }
        });

        this.modalCancelBtn?.addEventListener('click', () => {
            this.handleModalCancel();
        });
    }

    async handleModalOK() {
        if (!this.changeDate) return;

        // Convert and set start date
        this.startDate.value = await this.convertDateFormat(this.changeDate);

        const selectedOption = this.changeWindows.options[this.changeWindows.selectedIndex];
        const selectedText = selectedOption.textContent.trim();

        // Example: "Saturday 14:00:00 (12hrs)"
        const timeRegex = /\b(\d{2}:\d{2}(?::\d{2})?)\b/;
        const durationRegex = /\((\d+)hrs\)/;

        const timeMatch = selectedText.match(timeRegex);
        const durationMatch = selectedText.match(durationRegex);

        if (timeMatch) {
            const startTimeStr = timeMatch[1]; // e.g. "14:00:00"
            const parsedDateTime = DateTime.fromISO(`${this.startDate.value}T${startTimeStr}`);

            if (parsedDateTime.isValid) {
                this.startTime.value = parsedDateTime.toFormat('HH:mm');
            }
        }

        if (durationMatch) {
            const durationHours = parseInt(durationMatch[1], 10);

            const endDateTime = DateTime.fromISO(`${this.startDate.value}T${this.startTime.value}`)
                .plus({hours: durationHours});

            this.endTime.value = endDateTime.toFormat('HH:mm');
            this.endDate.value = endDateTime.toFormat('yyyy-MM-dd');

            this.durationSlider.value = durationHours;
            setSliderInitial(this.durationSlider, this.durationLabel, ChangeWindowClass.SLIDER_COLORS.DURATION);
        } else {
            // fallback: set end date to +1 day
            this.endDate.value = DateTime.fromISO(this.startDate.value)
                .plus({days: 1})
                .toFormat('yyyy-MM-dd');
        }
    }


    handleModalCancel() {
        if (this.changeInHoursBtn) {
            this.changeInHoursBtn.checked = true;
            this.changeInHoursBtnLabel?.click();
        }
    }

    setupFormListeners() {
        this.changeWindows?.addEventListener('change', async () => {
            this.enableChangeLeadtimeRadioButtons();
            await this.displayDateInModal();
        });

        this.changeWindowLeadTimeRadio.forEach(radio => {
            radio.addEventListener('click', async (event) => {
                try {
                    await this.handleLeadTimeChange(event.target.value);
                } catch (error) {
                    console.error('Error handling lead time change:', error);
                }
            });
        });
    }

    async handleLeadTimeChange(leadTimeValue) {
        this.leadtime = leadTimeValue;

        if (leadTimeValue === ChangeWindowClass.LEAD_TIME_WARNING_THRESHOLD) {
            await showSwal(
                'Change Window Lead Time',
                '<p>Other changes may occur in the intervening time that may affect the plans for this change. ' +
                'We recommend that, given the lead time, the change should be evaluated and brought to CAB ' +
                'closer to the expected change date.</p>',
                'info'
            );
        }

        await this.displayDateInModal();
        showFormButtons();
    }

    setupSliderListeners() {
        this.initializeSliders();
    }

    initializeSliders() {
        if (this.durationSlider && this.durationLabel) {
            setSliderInitial(this.durationSlider, this.durationLabel, ChangeWindowClass.SLIDER_COLORS.DURATION);
            this.setupSlider(this.durationSlider, this.durationLabel, {
                trackColor: ChangeWindowClass.SLIDER_COLORS.DURATION,
                additionalLogic: this.updateDurationSpecificLogic.bind(this)
            });
        }

        if (this.downtimeSlider && this.downtimeLabel) {
            setSliderInitial(this.downtimeSlider, this.downtimeLabel, ChangeWindowClass.SLIDER_COLORS.DOWNTIME);
            this.setupSlider(this.downtimeSlider, this.downtimeLabel, {
                trackColor: ChangeWindowClass.SLIDER_COLORS.DOWNTIME
            });
        }
    }

    setupSlider(slider, label, options = {}) {
        slider.addEventListener('input', () => {
            this.updateSliderAppearance(slider, label, options);
        });

        label.addEventListener('mousedown', (event) => {
            this.handleLabelDrag(event, slider, label, options);
        });
    }

    handleLabelDrag(initialEvent, slider, label, options) {
        const onMouseMove = (event) => {
            const rect = slider.getBoundingClientRect();
            const relativeX = event.clientX - rect.left;
            const percentage = Math.max(0, Math.min(1, relativeX / rect.width));

            const newValue = percentage * (slider.max - slider.min) + parseFloat(slider.min);
            slider.value = Math.min(Math.max(newValue, slider.min), slider.max);

            this.updateSliderAppearance(slider, label, options);
        };

        const onMouseUp = () => {
            document.removeEventListener('mousemove', onMouseMove);
            document.removeEventListener('mouseup', onMouseUp);
        };

        document.addEventListener('mousemove', onMouseMove);
        document.addEventListener('mouseup', onMouseUp);
    }

    updateSliderAppearance(slider, label, {trackColor, additionalLogic} = {}) {
        setSliderInitial(slider, label, trackColor);

        const value = Number(slider.value);
        slider.style.setProperty('--thumb-rotate', `${value * 100}deg`);

        const colorValue = ((value - slider.min) / (slider.max - slider.min)) * 100;
        slider.style.background =
            `linear-gradient(to right, ${trackColor} 0%, ${trackColor} ${colorValue}%, #ccc ${colorValue}%, #ccc 100%)`;

        if (additionalLogic) {
            additionalLogic(slider, value);
        }

        showFormButtons();
    }

    updateDurationSpecificLogic(slider, value) {
        const {endDateValue, endTimeValue} = this.calculateDateTime(value);
        if (this.endDate) this.endDate.value = endDateValue;
        if (this.endTime) this.endTime.value = endTimeValue;
    }

    calculateDateTime(hoursToAdd) {
        const now = new Date();
        let baseDateTime = new Date(now.getTime() + 7 * 24 * 60 * 60 * 1000); // Adding a week

        // Use existing start date/time if available
        if (this.startDate?.value && this.startTime?.value) {
            baseDateTime = new Date(`${this.startDate.value}T${this.startTime.value}`);
        } else {
            // Set default values if not present
            if (this.startDate) this.startDate.value = baseDateTime.toISOString().slice(0, 10);
            if (this.startTime) this.startTime.value = baseDateTime.toISOString().slice(11, 16);
        }

        // Calculate end datetime
        const endDateTime = new Date(baseDateTime.getTime() + hoursToAdd * 60 * 60 * 1000);

        return {
            endDateValue: endDateTime.toISOString().slice(0, 10),
            endTimeValue: endDateTime.toISOString().slice(11, 16)
        };
    }

    async convertDateFormat(inputDate) {
        try {
            const parsedDate = DateTime.fromFormat(inputDate, 'cccc LLL dd, yyyy');

            if (!parsedDate.isValid) {
                await showSwal('Invalid date format', 'Expected format: "Saturday, Oct 25, 2025".', 'error');
                return DateTime.local().toFormat('yyyy-MM-dd'); // fallback
            }

            return parsedDate.toFormat('yyyy-MM-dd'); // Output in ISO-style for form field
        } catch (error) {
            console.error('Error converting date format:', error);
            return DateTime.local().toFormat('yyyy-MM-dd'); // fallback
        }
    }


    async getDateForDay(weekday, occurrences = 1) {
        try {
            let targetWeekday;

            // Handle string weekday names
            if (!Number.isInteger(weekday)) {
                const normalized = weekday.charAt(0).toUpperCase() + weekday.slice(1).toLowerCase();
                targetWeekday = ChangeWindowClass.WEEKDAYS.indexOf(normalized);
            } else {
                targetWeekday = weekday;
            }

            if (targetWeekday < 0 || targetWeekday > 6) {
                await showSwal('Invalid weekday input', 'Please enter a valid weekday name or number.', 'error');
                return null;
            }

            const today = DateTime.local();
            const todayWeekdayLuxon = today.weekday % 7;

            const daysToAdd = (targetWeekday + 7 - todayWeekdayLuxon) % 7 + (occurrences - 1) * 7;
            const targetDate = today.plus({days: daysToAdd});

            return targetDate.toFormat('cccc LLL dd, yyyy'); // Example: "Saturday, Oct 25, 2025"
        } catch (error) {
            console.error('Error calculating date for day:', error);
            return null;
        }
    }


    disableChangeLeadtimeRadioButtons() {
        this.changeWindowLeadTimeRadio.forEach(radio => {
            radio.disabled = true;
        });
    }

    enableChangeLeadtimeRadioButtons() {
        this.changeWindowLeadTimeRadio.forEach(radio => {
            radio.disabled = false;
        });
    }
}