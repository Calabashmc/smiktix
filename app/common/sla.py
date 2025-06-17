from datetime import datetime, timedelta

from flask_login import current_user

from ..common.sla_calculator import SLACalculator  # library no longer maintained so copied here
from ..model import db
from ..model.model_user import User
from sqlalchemy import select
from ..model.lookup_tables import OfficeHours, PriorityLookup


def calculate_sla_times(create_time, priority='P3'):
    """
    Calculates response and resolve times using the sla_calculator library originally from here
    https://github.com/swimlane/sla_calculator
    but with the suggested merge on that site manually submitted as it seems to be unmaintained.
    Queries OfficeHours which only has 1 entry as SmikTix is intended for small business
    so unlikely to have IT staff in multiple locations across geography.
    A future update may change this???
    """
    user = db.session.get(User, current_user.id)

    if user and user.location:
        office_hours = user.location
    else:  # if User has not been assigned a location, use default. Assumes first record is default
        office_hours = db.session.execute(
            select(OfficeHours)
            .order_by(OfficeHours.id)
        ).scalars().first()

    sla_hours = db.session.execute(
        select(PriorityLookup)
        .where(PriorityLookup.priority == priority)
    ).scalars().first()

    sla_calc = SLACalculator(office_hours)

    respond_calc, resolve_calc = sla_calc.calculate_sla_times(
        start_time=str(create_time),
        response_hours=sla_hours.respond_by,
        resolve_hours=sla_hours.resolve_by,
        is_24hrs=sla_hours.twentyfour_seven
    )

    return respond_calc, resolve_calc


def calculate_resolve_time(response_time, wait_hours):
    """
    Calculate the resolve time based on a response time, wait hours, office hours, and weekends.

    Args:
        response_time (datetime): The time when the response was made.
        wait_hours (int): The working hours required for resolution.

    Returns:
        datetime: The calculated resolve time.
    """
    office_hours = db.session.execute(select(OfficeHours)).scalars().first()
    work_start = office_hours.open_hour
    work_end = office_hours.close_hour
    weekends = [6, 7]  # Saturday and Sunday

    response_time = datetime.strptime(response_time, '%Y-%m-%dT%H:%M')
    response_hour = response_time.time()

    # Adjust response time if it's outside working hours
    if response_hour < work_start or response_hour >= work_end:
        if response_hour >= work_end:
            # Move to the next workday
            response_time += timedelta(days=1)

        response_time = response_time.replace(hour=work_start.hour, minute=0, second=0, microsecond=0)

    remaining_hours = wait_hours
    result_response_time = response_time

    while remaining_hours > 0:
        # Skip weekends
        if result_response_time.isoweekday() in weekends:
            result_response_time += timedelta(days=1)
            result_response_time = result_response_time.replace(hour=work_start.hour, minute=0, second=0, microsecond=0)
            continue

        # Calculate hours available in the current workday
        end_of_day = result_response_time.replace(hour=work_end.hour, minute=work_end.minute, second=0, microsecond=0)
        hours_till_end_of_day = (end_of_day - result_response_time).total_seconds() / 3600

        if remaining_hours <= hours_till_end_of_day:
            # Resolve within the current workday
            result_response_time += timedelta(hours=remaining_hours)
            remaining_hours = 0
        else:
            # Move to the next workday
            remaining_hours -= hours_till_end_of_day
            result_response_time = end_of_day + timedelta(days=1)
            result_response_time = result_response_time.replace(hour=work_start.hour, minute=0, second=0, microsecond=0)
    return result_response_time.isoformat()
