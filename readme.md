# Office Tracker Agent

This script automatically calculates and tracks your mandatory office attendance targets based on the official Croatian calendar. It applies the rule of subtracting **10 allowed home days** from your personal working days to establish your monthly office target, tracks your progress from a local data file, and outputs a clean alignment report.

## Configuration

The script reads your personal logs from `/day_tracker.json`. Use the `YYYY-MM` format for keys, and populate day numbers as arrays of integers.

```json
{
  "yearly_vacation_allowance": 27,
  "carried_over_vacation_days": 6,

  "2026-06": {
    "out_of_office_days": [5],
    "planned_office_days": [1, 8, 9, 12, 16, 19, 23, 25, 29],
    "parking_booking_days": [1, 8, 9, 12, 16, 19]
  },
  "2026-07": {
    "out_of_office_days": [],
    "parking_booking_days": []
  },

  ...
}
```

## Execution

Before running the script, you must set up your virtual environment and verify the required dependencies.

### Environment Setup & Requirements Verification

Requirements are:

```text
pandas
holidays
openpyxl
```

Run the following commands in your terminal to initialize the environment and install dependencies:

```bash
# Create the virtual environment
python3.12 -m venv kounter-env

# Activate the virtual environment
source kounter-env/bin/activate

# Install required dependencies
pip install -r personal_scripts/requirements.txt
```

### Options for script execution

1. Run the script without parameters to evaluate your target progress using the current calendar date:

```bash
python kounter.py
```

2. Run the script with specific `YYYY-MM` parameters provisioned to simulate or plan for a different month. The script will automatically view the projection from the 1st day of that target month:

```bash
python personal_scripts/kounter.py  2026-07
```
