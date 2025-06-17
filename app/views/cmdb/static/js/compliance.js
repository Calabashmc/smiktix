import {tomSelectInstances} from "../../../../static/js/includes/tom-select.js";
import {showSwal} from "../../../../static/js/includes/form-classes/form-utils.js";

class ComplianceClass {
    constructor() {
        this.complianceSelect = document.getElementById("compliance-select");
        this.complianceList = document.getElementById("compliance-list");
        this.complianceAddBtn = document.getElementById("add-compliance-btn");
        this.complianceRemoveBtn = document.getElementById("remove-compliance-btn");
        this.ticketNumber = document.getElementById("ticket-number");
    }

    init() {
        this.setupListeners()
    }

    setupListeners() {
        this.complianceAddBtn.addEventListener("click", async () => {
            await this.handleAddCompliance();
        });

        this.complianceRemoveBtn.addEventListener("click", async () => {
            await this.handleRemoveCompliance();
        });
    }

    async handleAddCompliance() {
        const complianceSelect = this.complianceSelect.options[this.complianceSelect.selectedIndex]

        if (!complianceSelect.value) {
            await showSwal("Error", "Please select a compliance standard", "error");
            return;
        }

        const choice_txt = `${complianceSelect.text}`;
        const newOption = document.createElement("option");
        newOption.text = choice_txt;
        newOption.value = complianceSelect.value;
        this.complianceList.add(newOption);

        const tomInstance = tomSelectInstances.get(this.complianceSelect.id);
        if (tomInstance) {
            // Now you can safely call methods like removeOption
            tomInstance.removeOption(complianceSelect.value);
        } else {
            console.error('Tom Select instance not found for field:', fieldId);
        }

        const api_args = {
            "compliance_id": complianceSelect.value,
            "ticket_number": this.ticketNumber.value,
        }
        const response = await fetch("/api/cmdb/add-compliance/", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify(api_args),
        })
        const data = await response.json()
        if (!response.ok && data.error) {
            await showSwal("Error", data.error, "error");
        }
    }

    async handleRemoveCompliance() {
        const complianceListItem = this.complianceList.options[this.complianceList.selectedIndex];

        if (!complianceListItem) {
            await showSwal("Error", "Please select a compliance item to remove.", "error");
            return;
        }

        const api_args = {
            "compliance_id": complianceListItem.value,
            "ticket_number": this.ticketNumber.value,
        };

        const response = await fetch("/api/cmdb/remove-compliance", {
            method: "DELETE",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify(api_args),
        });

        const data = await response.json();

        if (!response.ok) {
            await showSwal("Error", data.error, "error");
            return;
        }

        const tomInstance = tomSelectInstances.get(this.complianceSelect.id);
        console.log(tomInstance)
        if (!tomInstance) {
            console.error("Tom Select instance not found for field:", this.complianceSelect.id);
            return;
        }

        // Add the removed item back to the Tom Select dropdown
        tomInstance.addOption({
            value: complianceListItem.value,
            text: complianceListItem.text,
        });

        // Remove the item from the list
        complianceListItem.remove();

    }

}

const complianceClass = new ComplianceClass()
complianceClass.init()