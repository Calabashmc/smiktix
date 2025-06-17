export class StatusStepper {
    constructor(containerId, steps) {
        this.container = document.getElementById(containerId);
        this.steps = steps;
        this.currentStep = 'new';
        this.render();
        this.updateStepStates();
    }

    createStepElement(step) {
        const stepDiv = document.createElement('div');
        stepDiv.className = 'step';

        const button = document.createElement('button');
        button.className = 'step-button';
        button.dataset.stepId = step.id;

        const iconCircle = document.createElement('div');
        iconCircle.className = 'step-icon-circle';
        iconCircle.innerHTML = `<i class='bi bi-${step.icon}'></i>`;

        const label = document.createElement('span');
        label.className = 'step-label';
        label.textContent = step.label;

        button.appendChild(iconCircle);
        button.appendChild(label);
        stepDiv.appendChild(button);

        // Add connector line
        const connector = document.createElement('div');
        connector.className = 'step-connector';
        stepDiv.appendChild(connector);

        button.addEventListener('click', () => this.handleStepClick(
            step.id,
            step.message == null ? '' : step.message,
            step.title == null ? '' : step.title,
            step.tabs == null ? [] : step.tabs)
        );

        return stepDiv;
    }

    isStepEnabled(stepId) {
        const currentStepObj = this.steps.find(step => step.id === this.currentStep);
        return stepId === this.currentStep || currentStepObj.allowedNext.includes(stepId);
    }

    handleStepClick(stepId, stepMessage, stepTitle, stepTabs) {
        if (this.isStepEnabled(stepId)) {
            this.currentStep = stepId;
            this.updateStepStates();

            // Emit change event
            const event = new CustomEvent('stepchange', {
                detail: {step: stepId, message: stepMessage, title: stepTitle, tabs: stepTabs}
            });
            this.container.dispatchEvent(event);
        }
    }

    updateStepStates() {
    const buttons = this.container.querySelectorAll('.step-button');
    let pastCurrent = true;
    const lastStepId = this.steps[this.steps.length - 1].id; // Get the last step ID

    buttons.forEach(button => {
        const stepId = button.dataset.stepId;
        button.classList.remove('current', 'enabled', 'completed', 'final-step');
        button.disabled = !this.isStepEnabled(stepId);

        if (stepId === 'new') {
            button.classList.add('completed'); // Mark first step as completed
            button.disabled = true;
        }

        if (stepId === this.currentStep) {
            button.classList.add('current');
            button.classList.remove('enabled');
            pastCurrent = false; // Stop marking as completed
        }
        if (this.isStepEnabled(stepId)) {
            button.classList.add('enabled');
        }
        if (pastCurrent) {
            button.classList.add('completed'); // Mark as completed
        }

        if (stepId === lastStepId && stepId === this.currentStep) {
            button.classList.add('final-step'); // Mark last step as red
        }
    });

    // Activate connectors for past steps
    const steps = Array.from(this.container.querySelectorAll('.step'));
    steps.forEach((step, index) => {
        const connector = step.querySelector('.step-connector');
        if (connector) {
            connector.classList.toggle('active', index < steps.findIndex(s => s.querySelector('.step-button.current')));
        }
    });
}


    render() {
        this.container.innerHTML = '';
        this.steps.forEach((step, index) => {
            const stepElement = this.createStepElement(step, index);
            this.container.appendChild(stepElement);
        });
    }

    getCurrentStep() {
        return this.currentStep;
    }

    setCurrentStep(stepId) {
        if (this.steps.find(step => step.id === stepId)) {
            this.currentStep = stepId;
            this.updateStepStates();
        }
    }

    /**
     * Returns the ID of the previous step based on the order in `steps`
     */
    getPreviousStep() {
        const currentIndex = this.steps.findIndex(step => step.id === this.currentStep);
        if (currentIndex > 0) {
            return this.steps[currentIndex - 1].id;
        }
        return null; // No previous step
    }
}
