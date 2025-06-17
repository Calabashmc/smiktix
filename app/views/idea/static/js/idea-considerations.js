import {showFormButtons} from "../../../../static/js/includes/form-classes/form-utils.js";

class IdeaConsiderationsClass {
    constructor() {
        this.estimatedEffortRadio = document.querySelectorAll("input[name='estimated_effort']");
        this.estimatedCostRadio = document.querySelectorAll("input[name='estimated_cost']");
    }

    init() {
        this.setupListeners();
    }

    setupListeners() {
        // Update label on slider input
        this.estimatedEffortRadio.forEach((radio) => {
            radio.addEventListener("change", () => {
                showFormButtons();
            });
        });

        // Similarly, set up listeners for the estimatedCostRadio if needed
        this.estimatedCostRadio.forEach((radio) => {
            radio.addEventListener("change", () => {
                showFormButtons();
            });
        });
    }
}

export const ideaConsiderationsClass = new IdeaConsiderationsClass();