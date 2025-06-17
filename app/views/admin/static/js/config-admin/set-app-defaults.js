import {showSwal} from "../../../../../static/js/includes/form-classes/form-utils.js";

class AppDefaults {
    constructor() {
        this.cancelBtn = document.getElementById("cancel-btn");
        this.changeRiskDefault = document.getElementById("change-default-risk");
        this.closeHour = document.getElementById("close-hour");
        this.impactDefault = document.getElementById("incident-default-impact");
        this.openHour = document.getElementById("open-hour");
        this.priorityDefault = document.getElementById("incident-default-priority");
        this.problemPriorityDefault = document.getElementById("problem-default-priority");
        this.saveBtn = document.getElementById("save-btn");
        this.serviceDeskEmail = document.getElementById("servicedesk-email");
        this.serviceDeskPhone = document.getElementById("servicedesk-phone");
        this.supportTeamDefaultId = document.getElementById("support-team-default-id");
        this.timezone = document.getElementById("timezone");
        this.urgencyDefault = document.getElementById("incident-default-urgency");
    }

    init() {
        this.cancelBtn.addEventListener("click", () => {
            location.reload();
        })

        this.changeRiskDefault.addEventListener("change", () => {
            this.enableSaveCancelBtns()
        });

        this.closeHour.addEventListener("change", () => {
            this.enableSaveCancelBtns()
        });

        this.impactDefault.addEventListener("change", () => {
            this.setPriority();
            this.enableSaveCancelBtns()
        });

        this.openHour.addEventListener("change", () => {
            this.enableSaveCancelBtns()
        });

        this.problemPriorityDefault.addEventListener("change", () => {
            this.enableSaveCancelBtns()
        });

        this.saveBtn.addEventListener("click", async () => {
            await this.setAppDefaults();
        });

        this.serviceDeskEmail.addEventListener("input", () => {
            this.enableSaveCancelBtns()
        });

        this.serviceDeskPhone.addEventListener("input", () => {
            this.enableSaveCancelBtns()
        });

        this.supportTeamDefaultId.addEventListener("change", () => {
            this.enableSaveCancelBtns()
        })

        this.timezone.addEventListener("input", () => {
            this.enableSaveCancelBtns()
        });

        this.urgencyDefault.addEventListener("change", () => {
            this.setPriority();
            this.enableSaveCancelBtns()
        });
    }

    enableSaveCancelBtns() {
        this.saveBtn.classList.remove("disabled");
        this.cancelBtn.classList.remove("disabled");
    }

    disableSaveCancelBtns() {
        this.saveBtn.classList.add("disabled");
        this.cancelBtn.classList.add("disabled");
    }

    setPriority() {
        const priorityMap = {
            "High": {"High": "P1", "Medium": "P2", "Low": "P3"},
            "Medium": {"High": "P2", "Medium": "P3", "Low": "P4"},
            "Low": {"High": "P3", "Medium": "P4", "Low": "P5"},
        };

        const impactValue = this.impactDefault.value;
        const urgencyValue = this.urgencyDefault.value;

        if (priorityMap[impactValue] && priorityMap[impactValue][urgencyValue]) {
            this.priorityDefault.value = priorityMap[impactValue][urgencyValue];
        }
    }

    async setAppDefaults() {
        const response = await fetch("/api/lookup/set-app-defaults/", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({
                "incident_default_priority": this.priorityDefault.value,
                "incident_default_impact": this.impactDefault.value,
                "incident_default_urgency": this.urgencyDefault.value,
                "problem_default_priority": this.problemPriorityDefault.value,
                "change_default_risk": this.changeRiskDefault.value,
                "service_desk_phone": this.serviceDeskPhone.value,
                "service_desk_email": this.serviceDeskEmail.value,
                "timezone": this.timezone.value,
                "service_desk_open_hour": this.openHour.value,
                "service_desk_close_hour": this.closeHour.value,
                "support_team_default_id": this.supportTeamDefaultId.value
            })
        })
        if (response.ok) {
            await showSwal("Success", "Defaults saved", "success");
            this.disableSaveCancelBtns()
        }
    }
}

export const appDefaults = new AppDefaults();