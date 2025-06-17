import pendulum
import holidays
from typing import Tuple


class SLACalculator:
    def __init__(self, office_hours):
        self.office_hours = office_hours
        self.holiday_calendar = set(holidays.country_holidays(
            office_hours.country_code,
            subdiv=office_hours.state or office_hours.province
        ).keys())

    def is_business_hours(self, dt: pendulum.DateTime, is_24hrs: bool) -> bool:
        """Check if the given datetime is within business hours, considering 24-hour operation."""
        if is_24hrs:
            return True  # Office is open 24/7, always within business hours

        dt = dt.in_timezone(self.office_hours.timezone)
        if dt.day_of_week in (pendulum.SATURDAY, pendulum.SUNDAY):
            return False
        if dt.date() in self.holiday_calendar:
            return False

        business_start = dt.replace(hour=self.office_hours.open_hour.hour, minute=self.office_hours.open_hour.minute)
        business_end = dt.replace(hour=self.office_hours.close_hour.hour, minute=self.office_hours.close_hour.minute)

        return business_start <= dt <= business_end

    def get_next_business_start(self, dt: pendulum.DateTime, is_24hrs: bool) -> pendulum.DateTime:
        """Get the next business start, considering 24-hour operation."""
        if is_24hrs:
            return dt  # Always return the current time if it's a 24-hour operation

        dt = dt.in_timezone(self.office_hours.timezone)
        business_start = dt.replace(hour=self.office_hours.open_hour.hour, minute=self.office_hours.open_hour.minute)

        if dt < business_start and dt.day_of_week < 5 and dt.date() not in self.holiday_calendar:
            return business_start

        return self.move_to_next_business_day(dt)

    def move_to_next_business_day(self, dt: pendulum.DateTime) -> pendulum.DateTime:
        """Find the next valid business day."""
        next_day = dt.add(days=1).start_of('day')
        while next_day.day_of_week in (pendulum.SATURDAY, pendulum.SUNDAY) or next_day.date() in self.holiday_calendar:
            next_day = next_day.add(days=1)
        return next_day

    def add_business_hours(self, start_time: pendulum.DateTime, hours: float, is_24hrs: bool) -> pendulum.DateTime:
        """Add business hours to the start time, considering 24-hour operation."""
        remaining_hours = hours
        current_time = start_time.in_timezone(self.office_hours.timezone)

        if not is_24hrs and not self.is_business_hours(current_time, is_24hrs):
            current_time = self.get_next_business_start(current_time, is_24hrs)

        while remaining_hours > 0:
            if is_24hrs:
                return current_time.add(hours=remaining_hours)

            day_end = current_time.replace(hour=self.office_hours.close_hour.hour,
                                           minute=self.office_hours.close_hour.minute)
            hours_today = day_end.diff(current_time).in_hours()

            if hours_today >= remaining_hours:
                return current_time.add(hours=remaining_hours)
            else:
                remaining_hours -= hours_today
                current_time = self.get_next_business_start(day_end, is_24hrs)

        return current_time

    def calculate_sla_times(self, start_time, response_hours: float, resolve_hours: float, is_24hrs: bool = False) -> \
            Tuple[pendulum.DateTime, pendulum.DateTime]:
        """Calculate SLA response and resolve times, considering 24-hour operation."""

        # Parse start_time if it's a string
        if isinstance(start_time, str):
            start_time = pendulum.parse(start_time)

        if is_24hrs:
            response_time = start_time.add(hours=response_hours)
            resolve_time = start_time.add(hours=resolve_hours)
        else:
            response_time = self.add_business_hours(start_time, response_hours, is_24hrs)
            resolve_time = self.add_business_hours(start_time, resolve_hours, is_24hrs)

        return response_time, resolve_time
