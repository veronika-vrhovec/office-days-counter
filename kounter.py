import datetime
import json
import os
import sys
import holidays
import pandas as pd


class OfficeTrackerAgent:

    def __init__(self, year: int, month: int, home_days_allowance: int = 10):
        self.year = year
        self.month = month
        self.home_days_allowance = home_days_allowance
        self.cro_holidays = holidays.HR(years=self.year)

    def get_days_breakdown(self) -> tuple:
        """Calculates working days, holidays on workdays, and holidays on weekends."""
        official_working_days = []
        holidays_on_workdays = 0
        holidays_on_weekends = 0
        num_days = pd.Period(f"{self.year}-{self.month}").days_in_month

        for day in range(1, num_days + 1):
            date_obj = datetime.date(self.year, self.month, day)

            if self.cro_holidays.get(date_obj) is not None:
                if date_obj.weekday() < 5:
                    holidays_on_workdays += 1
                else:
                    holidays_on_weekends += 1

            if (
                date_obj.weekday() < 5
                and self.cro_holidays.get(date_obj) is None
            ):
                official_working_days.append(date_obj)

        return official_working_days, holidays_on_workdays, holidays_on_weekends

    def track_office_metrics(
        self,
        out_of_office_days: list,
        parking_booking_days: list,
        evaluation_date: datetime.date,
    ):
        official_working_days, holidays_work, holidays_wknd = self.get_days_breakdown()
        num_days_in_month = pd.Period(f"{self.year}-{self.month}").days_in_month

        personal_working_days_count = len(official_working_days) - len(
            out_of_office_days
        )

        target_office_days_count = max(
            0, personal_working_days_count - self.home_days_allowance
        )

        actual_office_days_count = len(parking_booking_days)
        remaining_days_needed = max(
            0, target_office_days_count - actual_office_days_count
        )

        if target_office_days_count > 0:
            fulfillment_percentage = (
                actual_office_days_count / target_office_days_count
            ) * 100
        else:
            fulfillment_percentage = (
                100.0 if actual_office_days_count >= 0 else 0.0
            )

        # Dictionary to group working day counts by ISO week number
        weekly_breakdown = {}
        calendar_weeks_left = 0
        working_days_left_count = 0

        # --- TIMELINE TIMING LOGIC ---
        # 1. Past Months
        if (evaluation_date.year > self.year) or (
            evaluation_date.year == self.year
            and evaluation_date.month > self.month
        ):
            calendar_weeks_left = 0
            working_days_left_count = 0
            
        # 2. Future Months
        elif (evaluation_date.year < self.year) or (
            evaluation_date.year == self.year
            and evaluation_date.month < self.month
        ):
            for day in range(1, num_days_in_month + 1):
                date_obj = datetime.date(self.year, self.month, day)
                if (
                    date_obj.weekday() < 5
                    and self.cro_holidays.get(date_obj) is None
                ):
                    iso_wk = date_obj.isocalendar()[1]
                    weekly_breakdown[iso_wk] = weekly_breakdown.get(iso_wk, 0) + 1
                    working_days_left_count += 1
            calendar_weeks_left = len(weekly_breakdown)
            
        # 3. Current Active Month
        else:
            for day in range(evaluation_date.day, num_days_in_month + 1):
                date_obj = datetime.date(self.year, self.month, day)
                if (
                    date_obj.weekday() < 5
                    and self.cro_holidays.get(date_obj) is None
                ):
                    iso_wk = date_obj.isocalendar()[1]
                    weekly_breakdown[iso_wk] = weekly_breakdown.get(iso_wk, 0) + 1
                    working_days_left_count += 1
            calendar_weeks_left = len(weekly_breakdown)

        # Build the dynamic breakdown string if there are days left
        if working_days_left_count > 0:
            sorted_weeks = sorted(weekly_breakdown.keys())
            counts_list = [str(weekly_breakdown[w]) for w in sorted_weeks]
            workdays_string = f"{working_days_left_count} = " + " + ".join(counts_list)
        else:
            workdays_string = "0"

        return {
            "official_working_days": len(official_working_days),
            "personal_working_days": personal_working_days_count,
            "total_holidays": holidays_work,
            "weekend_holidays": holidays_wknd,
            "required_office_days": target_office_days_count,
            "actual_office_days": actual_office_days_count,
            "remaining_days_needed": remaining_days_needed,
            "calendar_weeks_left": calendar_weeks_left,
            "working_days_breakdown_str": workdays_string,
            "fulfillment_percentage": fulfillment_percentage,
        }


def load_agent_data(filename: str, lookup_key: str):
    """Safely loads data from JSON file for the given month key."""
    if not os.path.exists(filename):
        with open(filename, "w") as f:
            json.dump({}, f, indent=2)
        return [], []

    with open(filename, "r") as f:
        try:
            data = json.load(f)
            month_data = data.get(lookup_key, {})
            out_of_office = month_data.get("out_of_office_days", [])
            parking_bookings = month_data.get("parking_booking_days", [])
            return out_of_office, parking_bookings
        except json.JSONDecodeError:
            print(f"JSON format error. {json.JSONDecodeError}")
            return [], []


def load_vacation_allowance(filename: str) -> int:
    """Reads top-level annual allocation data out of the configuration tracker."""
    if not os.path.exists(filename):
        return 0
    with open(filename, "r") as f:
        try:
            data = json.load(f)
            yearly = data.get("yearly_vacation_allowance", 0)
            carried_over = data.get("carried_over_vacation_days", 0)
            return yearly + carried_over
        except json.JSONDecodeError:
            return 0


def print_monthly_report(month_key, metrics):
    """Prints formatting layout for a single month block with perfect alignments."""
    total_monthly_holidays = metrics['total_holidays'] + metrics['weekend_holidays']
    
    # If there are no holidays, use the clean string fallback format
    if total_monthly_holidays == 0:
        month_holidays_str = " 0 days"
    else:
        month_holidays_str = f"{total_monthly_holidays} = {metrics['total_holidays']} + {metrics['weekend_holidays']}"

    print(f"==================== AGENT REPORT ({month_key}) ====================")
    print(f"{'  Official working days in HR:':<38} {metrics['official_working_days']:>2} days")
    print(f"{'    Public holidays this month:':<38} {month_holidays_str}")
    print(f"{'    Personal working days:':<38} {metrics['personal_working_days']:>2} days")
    print(f"{'    Required office days (target):':<38} {metrics['required_office_days']:>2} days")
    print(f"{'    Days spent in office so far:':<38} {metrics['actual_office_days']:>2} days")
    print(f"{'    Target fulfillment:':<38} {metrics['fulfillment_percentage']:>5.1f}%")
    print(" -------------------------------------------------------------")

    if metrics["remaining_days_needed"] == 0:
        print("  Target met! Enough of the office for this month.")
    else:
        print(f"{'  Remaining office days to owe:':<38} {metrics['remaining_days_needed']:>2} days")
        print(f"{'    Calendar weeks left in month:':<38} {metrics['calendar_weeks_left']:>2} weeks")
        print(f"{'    Remaining workdays:':<39} {metrics['working_days_breakdown_str']}")
    print("================================================================\n")


def print_annual_summary(year, totals, remaining_vacation, adjusted_required_office, annual_fulfillment):
    """Prints aggregated year totals matching the column alignment width exactly."""
    total_calendar_holidays = totals['holidays_on_workdays'] + totals['holidays_on_weekends']
    holidays_str = f"{total_calendar_holidays} = {totals['holidays_on_workdays']} + {totals['holidays_on_weekends']}"
    
    print(f"=================== ANNUAL SUMMARY ({year}) ===================")
    print(f"{'  Total official working days:':<37} {totals['working_days']:>3} days")
    print(f"{'  Total public holidays:':<37} {holidays_str}")
    print(f"{'  Total allocation of vacation days:':<37} {totals['total_allocation']:>3} days")
    print(f"{'  Remaining vacation balance:':<37} {remaining_vacation:>3} days")
    print(f"{'  Total required days in office:':<37} {adjusted_required_office:>3} days")
    print(f"{'  Total days spent in office:':<37} {totals['actual_office']:>3} days")
    print(f"{'  Annual target fulfillment:':<37} {annual_fulfillment:>5.1f}%")
    print("=============================================================")


# --- Execution ---
if __name__ == "__main__":
    live_today = datetime.date.today()
    target_months = []
    is_full_year_run = False
    run_year = None

    if len(sys.argv) > 1:
        param = sys.argv[1].strip()

        if len(param) == 4 and param.isdigit():
            run_year = int(param)
            is_full_year_run = True
            print(f"Testing override mode enabled for entire year: {run_year}")
            for m in range(1, 13):
                target_months.append((run_year, m))
        else:
            try:
                parsed_year, parsed_month = map(int, param.split("-"))
                target_months.append((parsed_year, parsed_month))
                print(f"Testing override mode enabled for specified month: {param}")
            except (ValueError, IndexError):
                print(
                    "Invalid format provided. Please use YYYY-MM format (e.g., 2026-07) or YYYY format (e.g., 2026)."
                )
                print("Falling back to current live date...")
                target_months.append((live_today.year, live_today.month))
    else:
        target_months.append((live_today.year, live_today.month))

    script_dir = os.path.dirname(os.path.abspath(__file__))
    json_filename = os.path.join(script_dir, "../office_kounter/day_tracker.json")
    
    if not os.path.exists(json_filename):
        json_filename = "personal_scripts/office_kounter/day_tracker.json"

    print(
        f"Agent Status Check on: {live_today.strftime('%Y-%m-%d')} (Processing {len(target_months)} month(s))\n"
    )

    annual_totals = {
        "working_days": 0,
        "holidays_on_workdays": 0,
        "holidays_on_weekends": 0,
        "out_of_office": 0,
        "required_office": 0,
        "actual_office": 0,
        "total_allocation": 0
    }

    for year, month in target_months:
        current_month_key = f"{year}-{month:02d}"

        my_out_of_office_days, my_parking_bookings = load_agent_data(
            json_filename, current_month_key
        )

        agent = OfficeTrackerAgent(
            year=year, month=month, home_days_allowance=10
        )

        metrics = agent.track_office_metrics(
            out_of_office_days=my_out_of_office_days,
            parking_booking_days=my_parking_bookings,
            evaluation_date=live_today,
        )

        annual_totals["working_days"] += metrics["official_working_days"]
        annual_totals["holidays_on_workdays"] += metrics["total_holidays"]
        annual_totals["holidays_on_weekends"] += metrics["weekend_holidays"]
        annual_totals["out_of_office"] += len(my_out_of_office_days)
        annual_totals["required_office"] += metrics["required_office_days"]
        annual_totals["actual_office"] += metrics["actual_office_days"]

        print_monthly_report(current_month_key, metrics)

    if is_full_year_run:
        total_allocation = load_vacation_allowance(json_filename)
        annual_totals["total_allocation"] = total_allocation
        
        remaining_vacation_balance = total_allocation - annual_totals["out_of_office"]
        adjusted_required_office = max(0, annual_totals["required_office"] - remaining_vacation_balance)
        
        if adjusted_required_office > 0:
            annual_fulfillment = (annual_totals["actual_office"] / adjusted_required_office) * 100
        else:
            annual_fulfillment = 100.0 if annual_totals["actual_office"] >= 0 else 0.0
            
        print_annual_summary(run_year, annual_totals, remaining_vacation_balance, adjusted_required_office, annual_fulfillment)