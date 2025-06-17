import datetime
from config import Ticket, Session


def update_ticket_status():
    session = Session()

    resolved_tickets = session.query(Ticket).filter_by(status='Resolved').all()
    current_time = datetime.datetime.now()

    for ticket in resolved_tickets:
        if ticket.resolved_at and (current_time - ticket.resolved_at).days >= 3:
            ticket.status = 'Closed'
            ticket.worklog = (f'<span name="worklog-time">{current_time}'
                              f'</span>System automation set ticket status to "Closed" after 3 days of being "Resolved"'
                              f'<br>{ticket.worklog}')
            ticket.closed_at = current_time
            session.commit()

    session.close()


if __name__ == '__main__':
    update_ticket_status()
