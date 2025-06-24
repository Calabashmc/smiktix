import {formValidationListener} from './includes/validate-form.js';
import {JournalClass} from './includes/journal-class.js';
import {sunEditorClass} from './includes/suneditor-class.js';
import {formFieldHandlers} from './includes/form-classes/form-field-handlers.js';
import {formButtonHandlers} from './includes/form-classes/form-button-handlers.js';
import {requesterHandler} from './includes/form-classes/form-requester-handler.js';
import {ResolutionClass} from './includes/resolution-class.js';
import {exists, showFormButtons} from './includes/form-classes/form-utils.js';
import {initaliseTomSelectFields} from './includes/tom-select.js';

document.addEventListener('DOMContentLoaded', async function () {
    // **** load order matters here ***
    // to prevent change triggering when loading data into fields such as priority
    // and so journal sun-editor is created before formFieldHandlers which has onBlur
    await initaliseTomSelectFields();

    await sunEditorClass.setUpMultipleSunEditors('textarea.editor'); // create sun-editor instances

    if (exists) {
        const journalClass = new JournalClass();
        await journalClass.init(); // formats and populates timeline
    }

    // fieldStatusClass.init();
    await requesterHandler.init();
    await formFieldHandlers.init();
    formButtonHandlers.init();

    const resolutionClass = new ResolutionClass();
    resolutionClass.init();

    formValidationListener(); // validate form before saving

     // todo if I use this do I need to use 'dirty' class and call showFormButtons() elsewhere?
    const form = document.getElementById('form');
    if (form) {
        form.addEventListener('input', (event) => {
            if (event.target.classList.contains('dirty')) {
                showFormButtons();
            }
        });
    }
});

