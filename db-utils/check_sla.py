import datetime
from config import Ticket, Session


def check_sla_breach():
    """
    Checks for SLA Respond and Resolve breach and updates ticket Boolean for dashboard display
    :return: Nothing but ticket should be updated if SLA breached else does nothing
    """
    session = Session()
    from sqlalchemy import or_

    all_open_tickets = session.query(Ticket).filter(or_(Ticket.status == "New",
                                                        Ticket.status == "In Progress")).all()
    current_time = datetime.datetime.now()

    for ticket in all_open_tickets:
        if not ticket.sla_paused:
            if ticket.sla_respond_by < current_time:
                ticket.sla_response_breach = True
                ticket.worklog = (f'<span name="worklog-time">{current_time}'
                                  f'</span>SLA response time breached'
                                  f'<br>{ticket.worklog}')
                session.commit()

            if ticket.sla_resolve_by < current_time:
                ticket.sla_resolve_breach = True
                ticket.worklog = (f'<span name="worklog-time">{current_time}'
                                  f'</span>SLA resolution time breached'
                                  f'<br>{ticket.worklog}')
                session.commit()


if __name__ == '__main__':
    check_sla_breach()


def check_for_response_breach():
    pass