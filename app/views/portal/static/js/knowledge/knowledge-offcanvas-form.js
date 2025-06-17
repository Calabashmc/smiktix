import {sunEditorClass} from '../../../../../static/js/includes/suneditor-class.js';
import {showSwal} from '../../../../../static/js/includes/form-classes/form-utils.js';
import {getCurrentUser} from '../../../../../static/js/includes/utils.js';

export class KnowledgeOffcanvasFormClass {
    constructor() {
        this.articleType = document.getElementById('article-type');
        this.category = document.getElementById('article-category');
        this.offCanvasTitle = document.getElementById('offcanvas-title');
        this.shortDesc = document.getElementById('short-desc');
        this.title = document.getElementById('title');
        this.thumbsDownBtn = document.getElementById('thumbs-down');
        this.thumbsUpBtn = document.getElementById('thumbs-up');
    }

    init() {
        sunEditorClass.createSunEditor('article-details');
        this.setUpListeners();
    }

    setUpListeners() {
        this.thumbsUpBtn.addEventListener('click', async () => {
            await this.handleThumbsUp();
        })

        this.thumbsDownBtn.addEventListener('click', async () => {
            await this.handleThumbsDown();
        })
    }

    async showKbaOffcanvasForm(ticketNumber) {
        this.ticketNumber = ticketNumber;
        const kbaForm = new bootstrap.Offcanvas(document.querySelector('#portal-kba-article-offcanvas'), {focus: false});
        const response = await fetch(`/api/knowledge/get-knowledge-details/?ticket_number=${this.ticketNumber}`);
        const data = await response.json()

        this.thumbsDownBtn.disabled = false;
        this.thumbsUpBtn.disabled = false;

        this.category.innerHTML = data['article-category'];
        this.articleType.innerHTML = data['article-type'];

        const editorInstance = sunEditorClass.sunEditorInstances.get('article-details');
        if (editorInstance) {
            editorInstance.setContents(data['article-details']);
        } else {
            console.error('SunEditor instance not found for \'article-details\'');
        }


        this.shortDesc.innerHTML = data['short-desc'];
        this.title.innerHTML = data['title'];
        this.offCanvasTitle.innerHTML = `Knowledge Article ${this.ticketNumber}`
        kbaForm.show()
    }

    async handleThumbsUp() {
        const response = await fetch(`/api/knowledge/increment-knowledge-useful-count/?ticket_number=${this.ticketNumber}`);

        if (!response.ok) {
            console.error('Error incrementing useful count');
        } else {
            await showSwal('Thanks!', 'Thanks for the feedback', 'success');
            this.thumbsUpBtn.classList.add('animate__animated', 'animate__wobble');
            this.thumbsDownBtn.disabled = true;
            this.thumbsUpBtn.disabled = true;
            await window.portalKbaDashboardClass.refreshTables();
        }
    }

    async handleThumbsDown() {
        this.thumbsUpBtn.classList.add('animate__animated', 'animate__wobble');
        const {value: text} = await Swal.fire({
            icon: 'question',
            title: 'Feedback!',
            inputLabel: 'How can this article be improved?',
            input: 'textarea',
            inputPlaceholder: 'Type your message here...',
            inputAttributes: {
                'aria-label': 'Type your message here'
            },
            showCancelButton: true,
            customClass: {
                popup: 'sa-input-dialogue', // Add a custom class and style it accordingly
            },
            // Set a high z-index
            didOpen: () => {
                document.querySelector('.sa-input-dialogue').style.zIndex = 9999;
                document.querySelector('.swal2-input').focus();
            },
        })

        if (text) {
            const currentUser = await getCurrentUser()
            const apiArgs = {
                'details': text,
                'requester_id': currentUser['user_id'],
                'short_desc': `KBA Improvement - ${this.title.innerHTML}`,
                'ticket_type': 'request',
            }

            const response = await fetch('/api/knowledge/post-kba-improvement/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(apiArgs),
            })

            const data = await response.json()

            if (!response.ok) {
                await showSwal('Error', `Your feedback could not be submitted ${data['error']}`, 'error');
            } else {
                await showSwal('Thanks!', 'Your feedback has been submitted', 'success');
            }
        }
    }

}