import datetime
import holidays
import pandas as pd


class OfficeTrackerAgent:

    def __init__(self, year: int, month: int, home_days_allowance: int = 10):
        self.year = year
        self.month = month
        self.home_days_allowance = home_days_allowance

        # Initialize Croatian holidays
        self.cro_holidays = holidays.HR(years=self.year)

    def get_working_days(self) -> list:
        """Calculates actual working days (Mon-Fri) excluding Croatian public holidays."""
        working_days = []
        # Get number of days in the given month
        num_days = (
            pd.Period(f"{self.year}-{self.month}").days_in_month
        )  # Elegant way to get days in month

        for day in range(1, num_days + 1):
            date_obj = datetime.date(self.year, self.month, day)

            # Check if it's a weekday (0-4 is Mon-Fri) and not a holiday
            if date_obj.weekday() < 5 and date_obj not in self.cro_holidays:
                working_days.append(date_obj)

        return working_days

    def calculate_office_schedule(self):
        """Applies the rule:

        Office Days = Total Working Days - Home Days
        Then prepares the parking log basis.
        """
        all_working_days = self.get_working_days()
        total_working_days_count = len(all_working_days)

        # Your rule: target office days count
        target_office_days_count = max(
            0, total_working_days_count - self.home_days_allowance
        )

        # For the foundational script, we assume you take the first N working days as office days
        # Future agent logic can replace this with actual sensor data, calendar API, or manual logs
        office_days = all_working_days[:target_office_days_count]
        home_days = all_working_days[target_office_days_count:]

        return {
            "total_working_days": total_working_days_count,
            "target_office_days": target_office_days_count,
            "office_dates": office_days,
            "home_dates": home_days,
        }

    def generate_parking_excel(self, office_dates: list, filename: str = None):
        """Creates a DataFrame structured like an Excel sheet for parking tracking."""
        data = []

        for dt in office_dates:
            data.append(
                {
                    "Date": dt.strftime("%Y-%m-%d"),
                    "Day of Week": dt.strftime("%A"),
                    "Location": "Office",
                    "Parking Required": "YES",
                    "Spot Allocated": "",  # To be filled by agent/you later
                    "Status": "Pending",
                }
            )

        df = pd.DataFrame(data)

        if filename:
            df.to_excel(filename, index=False)
            print(f"📊 Parking sheet exported successfully to {filename}")

        return df


# --- Example Execution ---
if __name__ == "__main__":
    today = datetime.date.today()
    
    current_year = today.year
    current_month = today.month

    print(
        f"🤖 Initializing Tracker Agent for {current_year}-{current_month:02d}..."
    )
    agent = OfficeTrackerAgent(
        year=current_year, month=current_month, home_days_allowance=10
    )

    # Calculate metrics
    schedule = agent.calculate_office_schedule()

    print("\n--- Summary ---")
    print(f"Total potential working days (HR): {schedule['total_working_days']}")
    print(f"Required Office Days (minus 10):  {schedule['target_office_days']}")

"""
    # Generate the Excel data
    filename = f"parking_log_{current_year}_{current_month:02d}.xlsx"
    parking_df = agent.generate_parking_excel(
        schedule["office_dates"], filename=filename
    )

    print("\nPreview of the generated sheet structure:")
    print(parking_df.head())

"""