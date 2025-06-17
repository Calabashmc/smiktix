import pendulum
import holidays
from datetime import datetime, time
from typing import List


class BusinessHoursCalculator:
    """
    A class for calculating business hours within a given outage period. Accommodates for weekends and holidays based on
    country and region.

    Args:
        outage_start (datetime): The start date and time of the outage.
        outage_end (datetime): The end date and time of the outage.
        business_hours (List[time]): A list of tuples representing the start and end times of each business hour.
        country_code (str): The two-letter country code.
        timezone (str): The timezone of the country.

    Returns:
        float: The total business hours within the outage period. Returns days, hours, minutes by class method calls
    """
    def __init__(
            self,
            outage_start: datetime,
            outage_end: datetime,
            business_hours: List[time],
            country_code: str,
            timezone: str,
            state=None,
            province=None
    ):
        self.outage_start = outage_start
        self.outage_end = outage_end
        self.business_hours = sorted(business_hours)
        self.country_code = country_code
        self.timezone = timezone
        self.holidays = holidays.country_holidays(country_code, subdiv=state if state else province)

    def _is_business_day(self, dt: pendulum.DateTime) -> bool:
        return dt not in self.holidays and dt.weekday() < 5  # Monday-Friday

    def _is_within_business_hours(self, dt: pendulum.DateTime) -> bool:
        return (self._is_business_day(dt)
                and any(start <= dt.time() <= end
                        for start, end in
                        zip(self.business_hours[::2], self.business_hours[1::2])))

    def calculate_outage_in_business_hours(self, unit: str = "hours") -> float:
        tz = pendulum.timezone(self.timezone)
        start = pendulum.instance(self.outage_start, tz)
        end = pendulum.instance(self.outage_end, tz)
        total_business_minutes = 0

        current = start
        while current < end:
            if self._is_within_business_hours(current):
                next_minute = current.add(minutes=1)
                if next_minute <= end:
                    total_business_minutes += 1
            current = current.add(minutes=1)

        if unit == "days":
            return total_business_minutes / (60 * 8)  # Assuming an 8-hour business day
        elif unit == "hours":
            return total_business_minutes / 60  # Default to hours
        else:
            return total_business_minutes

    def get_days(self):
        return self.calculate_outage_in_business_hours(unit="days")

    def get_hours(self):
        return self.calculate_outage_in_business_hours(unit="hours")

    def get_minutes(self):
        return self.calculate_outage_in_business_hours(unit="minutes")
