import { showFormButtons, showSwal } from './form-classes/form-utils.js';

class SunEditorClass {
    constructor(containerIds, sunEditorOptions) {
        this.status = document.getElementById('status');
        this.sunEditorOptions = sunEditorOptions;
        this.ticketNumber = document.getElementById('ticket-number');
        this.ticketType = document.getElementById('ticket-type');

        this.minimumButtonList = [
            ['bold', 'underline', 'italic'],
            ['fontColor', 'hiliteColor'],
            ['removeFormat'],
            ['outdent', 'indent'],
            ['align', 'list'],
        ];

        this.normalButtonList = [
            ['fullScreen'],
            ['fontSize'],
            ['formatBlock'],
            ['bold', 'underline', 'italic'],
            ['fontColor', 'hiliteColor'],
            ['removeFormat'],
            ['outdent', 'indent'],
            ['align', 'horizontalRule', 'list'],
            ['table', 'image'],
        ];

        this.closedOptions = {
            buttonList: [...this.normalButtonList],
            width: '100%',
            resizeEnable: false,
            resizingBar: false,
        };

        this.timelineOptions = {
            autoResize: true,
            buttonList: [['saveBtn'], ...this.normalButtonList],
            fontSize: [12, 14, 16, 24],
            defaultStyle: 'font-size: 12pt;',
            fontSizeUnit: 'pt',
            hideToolbar: true,
            minHeight: '250px',
            maxHeight: '600px',
            plugins: [],
            resizeEnable: false,
            resizingBar: false,
            showPathLabel: false,
            width: '100%',
        };

        this.minimumOptions = {
            height: 'auto',
            minHeight: '50px',
            autoResize: true,
            width: '100%',
            fontSize: [12, 14, 16],
            defaultStyle: 'font-size: 12pt;',
            fontSizeUnit: 'pt',
            buttonList: this.minimumButtonList,
        };

        this.normalOptions = {
            height: 'auto',
            minHeight: '250px',
            autoResize: true,
            width: '100%',
            fontSize: [12, 14, 16, 24],
            defaultStyle: 'font-size: 12pt;',
            fontSizeUnit: 'pt',
            fullScreenOffset: 150,
            buttonList: this.normalButtonList,
            imageAccept: '.jpg, .png, .gif',
        };

        this.sunEditorInstances = new Map();
        this.journalInstances = new Map();
    }

    createSunEditor(id) {
        const area = document.getElementById(id);
        if (!area) return;

        let options = { ...this.normalOptions };

        // Determine editor type
        if (area.classList.contains('timeline-editor')) {
            const saveBtnPlugin = this._createSaveBtnPlugin(id);
            options = { ...this.timelineOptions };
            options.buttonList = [['saveBtn'], ...this.normalButtonList];
            options.plugins = [saveBtnPlugin];
        }

        if (area.classList.contains('minimum-editor')) {
            options = {...this.minimumOptions};
        }


        // Override if status is closed
        if (this.status?.value === 'closed') {
            options = { ...this.closedOptions };
        }

        // Prevent duplicate editors
        if (this.sunEditorInstances.has(id)) return;

        const editorInstance = SUNEDITOR.create(id, options);
        this.sunEditorInstances.set(id, editorInstance);
        this.setupListeners(area);

        if (area.classList.contains('timeline-editor')) {
            this.journalInstances.set(id, editorInstance);
            editorInstance.readOnly(true);
        }

        if (id === 'resolution-notes') {
            editorInstance.toolbar.show();
        }

        return editorInstance;
    }

    _createSaveBtnPlugin(editorId) {
        // Returns a plugin definition for the save button, bound to this instance
        return {
            name: 'saveBtn',
            display: 'command',
            innerHTML: '<i class="bi bi-floppy text-bg-success"></i>',
            buttonClass: '',
            add: function (core, targetElement) {
                const context = core.context;
                context.saveBtn = context.saveBtn || {};
                context.saveBtn.targetButton = targetElement;
                context.saveBtn.editorId = editorId;
                setTimeout(() => {
                    new bootstrap.Tooltip(targetElement, {
                        title: 'Save Changes',
                        placement: 'bottom',
                    });
                }, 100);
            },
            action: async () => {
                await this.saveNote(editorId);
            },
        };
    }

    setupListeners(area) {
        const editor = this.sunEditorInstances.get(area.id);
        if (!editor) return;

        if (!area.classList.contains('timeline-editor')) {
            editor.onInput = () => {
                showFormButtons();
            };
        } else {
            editor.onBlur = async () => {
                if (editor.core.isReadOnly) return;

                const response = await showSwal(
                    'Changes not saved',
                    'Save updates to the work note?',
                    'question'
                );

                if (response.isConfirmed) {
                    await this.saveNote(area.id);
                    editor.readOnly(true);
                    editor.toolbar.hide();
                } else {
                    editor.core.focus();
                }
            };

            editor.onChange = () => {
                this.changeContent = true;
            };
        }
    }

    async setUpMultipleSunEditors(editorClass) {
        const textAreas = document.querySelectorAll(editorClass);
        const textAreaIds = Array.from(textAreas).map(editor => editor.id);

        textAreaIds.forEach(id => this.createSunEditor(id));
    }

    checkSunEditorForContent(editorInstance) {
        if (!editorInstance) return false;
        const editorContents = editorInstance.getContents();
        const editorImages = editorInstance.getImagesInfo();
        const isEmpty = editorContents.replace(/<[^>]+>/g, '').trim();
        return isEmpty !== '' || editorImages.length !== 0;
    }

    clearSunEditorContent(id) {
        this.sunEditorInstances.get(id)?.setContents('');
    }

    disableAllEditors() {
        this.sunEditorInstances.forEach((editor, key) => {
            if (this.journalInstances.has(key)) return;
            editor.readOnly(true);
        });
    }

    enableAllEditors() {
        this.sunEditorInstances.forEach((editor, key) => {
            editor.readOnly(false);
            editor.toolbar.show();
            editor.setOptions({ ...this.normalOptions, resizingBar: true });
        });
    }

    enableSingleEditor(editorId) {
        const editorInstance = this.sunEditorInstances.get(editorId);
        if (editorInstance) {
            editorInstance.readOnly(false);
            editorInstance.toolbar.show();
            editorInstance.core.focus();
        }
    }

    disableSingleEditor(editorId) {
        const editorInstance = this.sunEditorInstances.get(editorId);
        if (editorInstance) {
            editorInstance.readOnly(true);
            editorInstance.toolbar.show();
            editorInstance.core.blur();
        }
    }

    destroySunEditor(id) {
        if (this.sunEditorInstances.has(id)) {
            const editor = this.sunEditorInstances.get(id);
            editor.destroy();
            this.sunEditorInstances.delete(id);
            this.journalInstances.delete(id);
        }
    }

    async saveNote(editorId) {
        const editor = this.sunEditorInstances.get(editorId);
        if (!editor) return;
        const updatedContent = editor.getContents();
        editor.toolbar.hide();
        editor.readOnly(true);

        const apiArgs = {
            record_id: editor.core.context.element.originElement.dataset.recordId,
            ticket_number: this.ticketNumber?.value,
            ticket_type: this.ticketType?.value,
            updated_note: updatedContent,
        };

        try {
            const response = await fetch('/api/update-worknote/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(apiArgs),
            });

            const result = await response.json();
            if (!response.ok) {
                await showSwal('Error', result['error'], 'error');
            }
        } catch (error) {
            console.error('Failed to update note:', error);
        }
    }
}

export const sunEditorClass = new SunEditorClass();