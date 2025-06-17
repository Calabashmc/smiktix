import datetime
from config import Ticket, Session, Notes


def set_child_status_to_match_parent():
    """
    Checks to see if tickets have a parent. If so sets their status to match the parents.
    In this way, when a parent is resolved or closed all child tickets are also set to this status.
    :return: Nothing
    """
    session = Session()
    all_tickets = session.query(Ticket).all()

    current_time = datetime.datetime.now()
    for ticket in all_tickets:
        if ticket.parent_id:
            ticket.status = ticket.parent.status
            ticket.last_updated_at = current_time

            if ticket.status == "Resolved" or ticket.status == "Closed":
                ticket.resolved_at = ticket.parent.resolved_at
                ticket.closed_at = ticket.parent.closed_at
                ticket.resolution_code_id = ticket.parent.resolution_code_id
                ticket.resolution_notes = f"Refer to parent ticket {ticket.parent_id} for resolution notes"

            worklog_note = (f'Fields updated via automation with details from '
                            f'Parent Ticket number {ticket.parent_id}'
                            )

            worklog = Notes(note=worklog_note,
                            noted_by="Automation",
                            note_date=datetime.datetime.now(),
                            ticket_number=ticket.ticket_number
                            )

            ticket.notes.append(worklog)

            session.commit()


if __name__ == '__main__':
    set_child_status_to_match_parent()
