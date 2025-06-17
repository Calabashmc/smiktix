export class ChangeRiskClass {
    constructor() {
        this.changeHoursRadio = document.querySelectorAll('input[name="change-hours-radio"]')
        this.changeScale = document.getElementById('change-scale');
        this.ciImpacted = document.getElementById('cmdb-id');

        this.downtimeSlider = document.getElementById('change-downtime');
        this.durationSlider = document.getElementById('change-duration');

        this.peopleImpactCheck = document.getElementById('people-impact');
        this.riskCalc = document.getElementById('risk-calc');

        // risk inputs
        this.checkboxes = document.querySelectorAll('.accordion-item .accordion-header input[type="checkbox"]');
        this.displaySpans = document.querySelectorAll('.impact-likelihood-display');
        this.riskRadios = document.querySelectorAll('.accordion-item .accordion-body input[type="radio"]')

    }

    async init() {
        await this.setRiskLevel();
        this.setUpListeners()
        this.initialiseDisplay();
        this.initializeDefaultRadioValues();
    }

    initializeDefaultRadioValues() {
        this.checkboxes.forEach(checkbox => {
            const baseId = checkbox.id;
            const impactName = `${baseId}_impact`;
            const likelihoodName = `${baseId}_likelihood`;

            // Check if no radio is selected for impact
            const impactChecked = document.querySelector(`input[name="${impactName}"]:checked`);
            if (!impactChecked) {
                const defaultImpact = document.querySelector(`input[name="${impactName}"][value="Low"]`);
                if (defaultImpact) {
                    defaultImpact.checked = true;
                } else {
                    console.warn(`Could not find default impact radio for ${baseId}`);
                }
            }

            // Check if no radio is selected for likelihood
            const likelihoodChecked = document.querySelector(`input[name="${likelihoodName}"]:checked`);
            if (!likelihoodChecked) {
                const defaultLikelihood = document.querySelector(`input[name="${likelihoodName}"][value="Low"]`);
                if (defaultLikelihood) {
                    defaultLikelihood.checked = true;
                } else {
                    console.warn(`Could not find default likelihood radio for ${baseId}`);
                }
            }
        });
    }

    setUpListeners() {
        // risk calculation accordion
        this.checkboxes.forEach(checkbox => {
            checkbox.addEventListener('change', async (e) => {
                const accordionTarget = e.target.getAttribute('data-bs-target');
                const accordionInstance = new bootstrap.Collapse(accordionTarget, {toggle: false});

                await this.setRiskLevel(e);
                this.initialiseDisplay()

                if (!e.target.checked) {
                    accordionInstance.hide()
                } else {
                    accordionInstance.show()
                }
            });
        });

        // change timing
        this.changeHoursRadio.forEach(radio => {
            radio.addEventListener('click', async () => {
                await this.setRiskLevel();
            });
        });

        // other risk calculation fields and controls
        [
            this.changeScale,
            this.ciImpacted,
            this.downtimeSlider,
            this.durationSlider,
            this.peopleImpactCheck
        ].forEach(element => element?.addEventListener('change', () => this.setRiskLevel()));

        // risk radio for user to select risk level
        this.riskRadios.forEach(radio => {
            radio.addEventListener('click', async () => {
                await this.setRiskLevel();
            });
        });
    }

    initialiseDisplay() {
        // Initial updates of a
        this.displaySpans.forEach(span => {
            this.updateImpactProbabilityDisplay(span)
        });
    }

    // updates the accordion header to show impact and likelihood without needed to open the accordion
    updateImpactProbabilityDisplay(displaySpan) {
        const impactCheckBoxId = displaySpan.getAttribute('data-target-checkbox'); // Get the ID of the checkboxId
        const impactCheckBox = document.getElementById(impactCheckBoxId);
        const impactCheckBoxValue = document.getElementById(`${impactCheckBoxId}_impact_span`)

        const impactFieldId = displaySpan.getAttribute('data-target-impact');
        const likelihoodFieldId = displaySpan.getAttribute('data-target-likelihood');
        const likelihoodCheckBoxValue = document.getElementById(`${impactCheckBoxId}_likelihood_span`)

        if (impactCheckBox.checked) {
            const impactField = document.querySelector(`input[name='${impactFieldId}']:checked`);
            const likelihoodField = document.querySelector(`input[name='${likelihoodFieldId}']:checked`);
            impactCheckBoxValue.parentElement.disabled = false;
            impactCheckBoxValue.innerText = impactField.value;
            likelihoodCheckBoxValue.innerText = likelihoodField.value;
        } else {
            impactCheckBoxValue.parentElement.disabled = true;
            impactCheckBoxValue.innerText = '--';
            likelihoodCheckBoxValue.innerText = '--';
        }

    }

    // Function to update the risk field based on conditions
    async setRiskLevel() {
        let risks = {};
        for (const checkbox of this.checkboxes) {
            if (checkbox.checked) {
                // If the checkbox is checked, get the associated data
                const dataParent = checkbox.id; // E.g., 'risk-security'
                const impact = document.querySelector(`input[name='${dataParent}_impact']:checked`)?.value || 'Low';
                const likelihood = document.querySelector(`input[name='${dataParent}_likelihood']:checked`)?.value || 'Low';

                // // Package the data
                risks[dataParent] = {
                    [`${dataParent}-impact`]: impact,
                    [`${dataParent}-likelihood`]: likelihood
                };
            }
        }

        let change_timing = 'in_hours'; // set default
        this.changeHoursRadio.forEach(radio => {
            if (radio.checked) {
                change_timing = radio.value
            }
        });

        const apiArgs = {
            'change_timing': change_timing,
            'risk': risks,
            'ci_id': this.ciImpacted.value,
            'downtime': this.downtimeSlider.value,
            'duration': this.durationSlider.value,
            'people_impact': this.peopleImpactCheck.value,
            'scale': this.changeScale.value,
        };

        const response = await fetch('/api/change/set-calculated-risk/', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(apiArgs)
        });

        const data = await response.json();
        if (response.ok) {
            this.riskCalc.value = data['risk'];
        } else {
            this.riskCalc.value = 'CR5';
        }
        this.riskCalc.dispatchEvent(new Event('change'));
        this.initialiseDisplay()
    }
}
