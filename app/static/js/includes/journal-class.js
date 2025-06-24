import {sunEditorClass} from './suneditor-class.js';

export class JournalClass {
    constructor() {
        // Cache DOM elements
        this.elements = {
            timeline: this.getById('timeline'),
            systemTimeline: this.getById('system-timeline'),
            ticketNumber: this.getById('ticket-number'),
            ticketType: this.getById('ticket-type'),
            status: this.getById('status')
        };

        // Track active editors for clean-up
        this.activeEditors = new Set();

        // Initialize lazy loading observer
        this.initLazyEditorObserver();

        // Store note ID mapping for consistent referencing
        this.noteIdMap = new Map();
    }

    getById(id) {
        const element = document.getElementById(id);
        if (!element) {
            throw new Error(`Element with ID '${id}' not found`);
        }
        return element;
    }

    async init() {
        await this.journalTimeline();
        this.setupListeners();
    }

    setupListeners() {
        // custom event triggered when worklog is saved in form-utils.js
        document.addEventListener('worklog-saved', async () => {
            await this.journalTimeline();
        });
    }

    async journalTimeline() {
        const apiArgs = {
            ticket_number: this.elements.ticketNumber.value,
            ticket_type: this.elements.ticketType.value,
        };

        try {
            const data = await this.fetchWorkNotes(apiArgs);

            if (!data || data.length === 0) {
                this.clearTimelines();
                console.log('No data received');
                return;
            }

            this.renderTimeline(data);

        } catch (error) {
            console.error('Error loading journal timeline:', error);
            await this.showError('Failed to load journal timeline', error.message);
        }
    }

    async fetchWorkNotes(apiArgs) {
        const response = await fetch('/api/get-worknotes/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(apiArgs),
        });

        const data = await response.json();

        if (!response.ok) {
            await this.showError('Error', data.error || 'Unknown error occurred');
            throw new Error(data.error || 'API request failed');
        }

        return data;
    }

    renderTimeline(data) {
        // Clear existing content and clean-up editors
        this.clearTimelines();
        this.cleanupEditors();
        this.noteIdMap.clear();

        // Use document fragments for better performance
        const timelineFragment = document.createDocumentFragment();
        const systemTimelineFragment = document.createDocumentFragment();

        const isReadOnly = this.isReadOnlyStatus();

        for (const item of data) {
            const noteLi = this.createTimelineItem(item, isReadOnly);

            if (item.is_system) {
                systemTimelineFragment.appendChild(noteLi);
            } else {
                timelineFragment.appendChild(noteLi);
            }
        }

        // Single DOM update per timeline
        this.elements.timeline.appendChild(timelineFragment);
        this.elements.systemTimeline.appendChild(systemTimelineFragment);

        // Initialize lazy loading for editors
        this.initialiseEditors();
    }

    createTimelineItem(item, isReadOnly) {
        const noteLi = document.createElement('li');
        const noteId = this.generateNoteId();

        // Store the mapping for consistent reference
        this.noteIdMap.set(item.record_id, noteId);

        const timeStamp = this.createTimestamp(item, noteId, isReadOnly);
        const noteContainer = this.createNoteContainer(item, noteId);

        noteLi.appendChild(timeStamp);
        noteLi.appendChild(noteContainer);

        return noteLi;
    }

    createTimestamp(item, noteId, isReadOnly) {
        const timeStamp = document.createElement('div');
        timeStamp.className = 'worklog-time';

        if (item.is_system || isReadOnly) {
            timeStamp.textContent = `${item.note_date} by: ${item.noted_by}`;
        } else {
            const editIcon = document.createElement('a');
            editIcon.id = `${noteId}-btn`;
            editIcon.className = 'bi bi-pencil-square me-2';
            editIcon.setAttribute('role', 'button');
            editIcon.setAttribute('tabindex', '0');
            editIcon.setAttribute('aria-label', 'Edit note');

            const dateText = document.createTextNode(` ${item.note_date} by: ${item.noted_by}`);

            timeStamp.appendChild(editIcon);
            timeStamp.appendChild(dateText);
        }

        return timeStamp;
    }

    createNoteContainer(item, noteId) {
        const noteContainer = document.createElement('div');

        noteContainer.id = noteId;
        noteContainer.dataset.content = item.note;
        noteContainer.dataset.recordId = item.record_id;

        if (item.is_system) {
            noteContainer.className = 'system-journal-entry timeline-editor';
            // Use lazy loading for system entries too
            noteContainer.innerHTML = '<div class="editor-loading">Loading editor...</div>';
        } else {
            noteContainer.className = 'journal-entry timeline-editor';
            noteContainer.innerHTML = '<div class="editor-loading">Loading editor...</div>';
        }

        return noteContainer;
    }

    initialiseEditors() {
        // Observe both regular and system timeline editors
        const regularEditors = this.elements.timeline.querySelectorAll('.timeline-editor');
        const systemEditors = this.elements.systemTimeline.querySelectorAll('.timeline-editor');

        [...regularEditors, ...systemEditors].forEach(container => {
            this.editorObserver.observe(container);
        });
    }

    initialiseEditor(noteContainer) {
        const noteId = noteContainer.id;
        const journalNote = noteContainer.dataset.content;

        try {
            // Clean up existing editor if it exists
            if (sunEditorClass.sunEditorInstances.has(noteId)) {
                sunEditorClass.destroySunEditor(noteId);
            }

            // Remove loading indicator
            noteContainer.innerHTML = '';

            const editor = sunEditorClass.createSunEditor(noteId);
            editor.setContents(journalNote);

            this.activeEditors.add(noteId);
            noteContainer.classList.remove('timeline-editor');
            noteContainer.classList.add('editor-initialized');

            // Clean up data attributes to prevent memory leaks
            delete noteContainer.dataset.content;

            this.attachEditListener(noteId);

        } catch (error) {
            console.error(`Failed to initialize editor for ${noteId}:`, error);
            noteContainer.innerHTML = '<div class="editor-error">Failed to load editor</div>';
        }
    }

    attachEditListener(noteId) {
        const editBtn = document.getElementById(`${noteId}-btn`);
        if (editBtn) {
            const clickHandler = (e) => {
                e.preventDefault();
                this.editNote(noteId);
            };

            const keyHandler = (e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    this.editNote(noteId);
                }
            };

            // Remove existing listeners to prevent duplicates
            editBtn.removeEventListener('click', clickHandler);
            editBtn.removeEventListener('keydown', keyHandler);

            // Add new listeners
            editBtn.addEventListener('click', clickHandler);
            editBtn.addEventListener('keydown', keyHandler);
        }
    }

    editNote(noteId) {
        try {
            sunEditorClass.enableSingleEditor(noteId);
        } catch (error) {
            console.error(`Failed to enable editor ${noteId}:`, error);
        }
    }

    initLazyEditorObserver() {
        if (this.editorObserver) return; // Avoid reinitializing

        const options = {
            root: null, // viewport
            rootMargin: '50px', // Start loading 50px before element enters viewport
            threshold: 0.1 // Trigger when 10% of the element is visible
        };

        this.editorObserver = new IntersectionObserver((entries) => {
            for (const entry of entries) {
                if (entry.isIntersecting) {
                    const container = entry.target;
                    this.initialiseEditor(container);
                    this.editorObserver.unobserve(container); // Stop observing once initialised
                }
            }
        }, options);
    }

    // Helper methods
    isReadOnlyStatus() {
        const status = this.elements.status.value;
        return status === 'closed' || status === 'resolved';
    }

    generateNoteId() {
        return crypto.randomUUID();
    }

    sanitizeContent(content) {
        if (!content) return '';

        // Basic HTML sanitization - consider using DOMPurify for production
        const div = document.createElement('div');
        div.textContent = content;
        return div.innerHTML;
    }

    clearTimelines() {
        this.elements.timeline.innerHTML = '';
        this.elements.systemTimeline.innerHTML = '';
    }

    cleanupEditors() {
        // Disconnect observer to prevent memory leaks
        if (this.editorObserver) {
            this.editorObserver.disconnect();
        }

        // Clean up editor instances
        for (const editorId of this.activeEditors) {
            if (sunEditorClass.sunEditorInstances.has(editorId)) {
                sunEditorClass.destroySunEditor(editorId);
            }
        }
        this.activeEditors.clear();
    }

    async showError(title, message) {
        if (typeof showSwal === 'function') {
            await showSwal(title, message, 'error');
        } else {
            console.error(`${title}: ${message}`);
            alert(`${title}: ${message}`);
        }
    }

    // Clean-up method to be called when component is destroyed
    destroy() {
        this.cleanupEditors();
        this.noteIdMap.clear();

        if (this.editorObserver) {
            this.editorObserver.disconnect();
            this.editorObserver = null;
        }
    }
}
