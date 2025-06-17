import {showSwal} from "../../../../static/js/includes/form-classes/form-utils.js";

class ChangeFreeze {
    constructor() {
        this.addChangeFreezeBtn = document.getElementById("add-change-freeze-btn");
        this.changeFreezeEndDate = document.getElementById("change-freeze-end-date");
        this.changeFreezeList = document.getElementById("change-freeze-list");
        this.changeFreezeReason = document.getElementById("change-freeze-reason");
        this.changeFreezeStartDate = document.getElementById("change-freeze-start-date");
        this.changeFreezeTitle = document.getElementById("change-freeze-title");
        this.removeChangeFreezeBtn = document.getElementById("remove-change-freeze-btn");
        this.ticketNumber = document.getElementById("ticket-number");
    }

    init() {
        this.setUpListeners();
    }

    setUpListeners() {
        this.addChangeFreezeBtn.addEventListener("click", async () => {
            await this.addChangeFreeze()
        });

        this.removeChangeFreezeBtn.addEventListener("click", async () => {
            await this.removeChangeFreeze()
        });
    }

    async addChangeFreeze() {
        const startDate = this.changeFreezeStartDate.value;
        const endDate = this.changeFreezeEndDate.value;
        const reason = this.changeFreezeReason.options[this.changeFreezeReason.selectedIndex].text;
        const title = this.changeFreezeTitle.value;

        if (!startDate || !endDate || !reason || !title) {
            await showSwal("Error", "All Change Freeze fields are required", "error");
            return;
        }

        const api_args = {
            "end_date": endDate,
            "reason": reason,
            "start_date": startDate,
            "ticket_number": this.ticketNumber.value,
            "title": title
        }

        const response = await fetch("/api/cmdb/add-change-freeze/", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(api_args)
        })

        const data = await response.json();

        if (data.error) {
            await showSwal("Error", data.error, "error");
        } else {
            // Helper function to pad or truncate the title
            function formatTitle(title, width = 15, padChar = "\u00A0") {
                if (title.length > width) {
                    return title.slice(0, width); // Truncate if too long
                }
                return title.padEnd(width, padChar); // Pad with the specified character if too short
            }


            // Formatting logic
            const formattedTitle = formatTitle(title);
            const formattedReason = formatTitle(reason, 22);
            const formattedStartDate = startDate.padEnd(10, " "); // Ensure 10 characters width
            const formattedEndDate = endDate.padEnd(10, " ");     // Ensure 10 characters width

            // Construct the choice text
            const choice_txt = `${formattedTitle} ${formattedReason}  ${formattedStartDate} to ${formattedEndDate}`;

            const newOption = document.createElement("option");
            newOption.text = choice_txt;
            newOption.value = data.response["id"];
            this.changeFreezeList.add(newOption);
        }
    }

    async removeChangeFreeze() {
        if (!this.changeFreezeList || this.changeFreezeList.selectedIndex === -1) {
            await showSwal("Error", "Please select a Change Freeze to remove", "error");
            return;
        }
        const freeze = this.changeFreezeList.options[this.changeFreezeList.selectedIndex].value

        const api_args = {
            "freeze": freeze,
        }

        const response = await fetch("/api/cmdb/remove-change-freeze/", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(api_args)
        })

        const data = await response.json();

        if (data.error) {
            await showSwal("Error", data.error, "error");
        } else {
            this.changeFreezeList.remove(this.changeFreezeList.selectedIndex);
        }
    }
}

const changeFreeze = new ChangeFreeze();
changeFreeze.init();