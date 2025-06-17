// noinspection JSValidateTypes
class KnowledgeClass {
    constructor() {
        this.created = document.getElementById('created');
        this.published = document.getElementById('published');
        this.reviewed = document.getElementById('reviewed');
        this.ticketNumber = document.getElementById('ticket-number');
        this.useful = document.getElementById('useful');
        this.viewed = document.getElementById('viewed');
    }

    async init() {
        await this.populateInfo();
    }

    async populateInfo() {
        const response = await fetch('/api/knowledge-ticket-info/', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 'ticket_number': this.ticketNumber.value })
        });

        const data = await response.json();

        this.created.textContent = data['created'];
        this.published.textContent = data['published'];
        this.reviewed.textContent = data['reviewed'];
        this.useful.textContent = data['useful'];
        this.viewed.textContent = data['viewed'];
    }
}

export const knowledgeClass = new KnowledgeClass()
