from datetime import datetime, timedelta
import pandas as pd

def format_mins(minutes):
    hours = minutes // 60
    mins = minutes % 60
    if hours > 0 and mins > 0:
        return f"{hours} hr {mins} min"
    
    elif hours > 0:
        return f"{hours} hr"
    
    else:
        return f"{mins} min"


def generate_schedule(assignments, availability, use_minutes=True):
    today = datetime.today().date()

    # collect data
    study_days = set()

    for a in assignments:
        due = a["due_date"]

        for i in range((due - today).days + 1):
            study_days.add(today + timedelta(days=i))

    study_days = sorted(list(study_days))

    # build map
    daily_slots = []
    for day in study_days:
        weekday = day.strftime("%A")
        mins_avail = availability.get(weekday, 0)

        if mins_avail > 0:
            daily_slots.append({"date": day, "weekday": weekday, "max_minutes": mins_avail, "free_minutes": mins_avail})


    if not daily_slots:
        raise ValueError("No available days to schedule work.")

    schedule = []
    
    for part in assignments:
        remaining = part.get("minutes_required") if use_minutes else int(part.get("hours_required", 0) * 60)
        course = part["course"]
        task = part["task"]
        due = part["due_date"]

        # check elegibility and days
        eligible_days = [date for date in daily_slots if date["date"] <= due and date["free_minutes"] > 0]
        total_avail = sum(date["free_minutes"] for date in eligible_days)

        if total_avail < remaining:
            raise ValueError(f"Not enough time to complete '{task}' before {due}.")

        # allocation distributions
        allocations = []
        for day in eligible_days:
            proportion = day["free_minutes"] / total_avail
            alloc = round(proportion * remaining)
            allocations.append(min(alloc, day["free_minutes"]))

        # greedy for rounding error
        total_alloc = sum(allocations)
        diff = remaining - total_alloc
        i = 0
        while diff != 0:

            if diff > 0:
                # add one try

                if allocations[i] < eligible_days[i]["free_minutes"]:
                    allocations[i] += 1
                    diff -= 1

            else:
                if allocations[i] > 0:
                    allocations[i] -= 1
                    diff += 1

                    
            i = (i + 1) % len(allocations)

        # assign minutes and build schedule
        for alloc, day in zip(allocations, eligible_days):
            if alloc > 0:
                schedule.append({
                    "Date": day["date"].strftime("%Y-%m-%d"),
                    "Weekday": day["weekday"],
                    "Course": course,
                    "Assignment": task,
                    "Minutes": alloc,
                    "Time": format_mins(alloc)
                })
                day["free_minutes"] -= alloc

    df = pd.DataFrame(schedule)
    df = df.sort_values(by=["Date", "Course"]).reset_index(drop=True)
    return df
