"""
Transform stage: builds the relational model of the company from the two
sources.

What comes from the data, and what is generated
------------------------------------------------
REAL (IBM HR Analytics, realistic relationships between variables):
  department, job role, job level, salary, last raise %, overtime, business
  travel, distance from home, education, satisfaction / involvement /
  work-life-balance scores, performance rating, number of trainings last
  year, years at company / in role / since promotion / with manager, total
  working years, number of previous employers, stock options, who left.
REAL (Kaggle Resume dataset): the applicants' resumes (text + PDF, category).

DERIVED from the data (rules, documented below):
  teams and team leaders, manager hierarchy, application roles, titles,
  hire / exit dates (from the years columns), exit reasons (from each
  leaver's own data), salary history (from the last raise %), job openings
  (where people actually left), required experience and salary range of the
  openings (from the employees in the same role), which job each resume
  applies to (from its category).

GENERATED (identifiers only, no analysis uses them):
  names, emails, phone numbers, exact days inside a year, training course
  chosen for each training, recruitment funnel statuses.
"""

import math
import uuid
from datetime import datetime, timezone

import numpy as np
import pandas as pd

import config
from identity import IdentityFactory
from job_title_skills import skills_for_title


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def snapshot_date() -> pd.Timestamp:
    if config.SNAPSHOT_DATE:
        return pd.Timestamp(config.SNAPSHOT_DATE).normalize()
    return pd.Timestamp.now().normalize()


def _now_str():
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")


def _days(rng, lo, hi):
    return pd.Timedelta(days=int(rng.integers(lo, hi + 1)))


def _plural(role: str) -> str:
    return {"Human Resources": "HR Specialists", "Manager": "Managers",
            "Research Director": "Research Directors"}.get(role, role + "s")


def job_title(role: str, level: int, department: str) -> str:
    """Readable title from the IBM role + job level (1-5)."""
    if role == "Manager":
        dept = {"Research & Development": "R&D", "Sales": "Sales", "Human Resources": "HR"}[department]
        return {3: f"{dept} Manager", 4: f"Senior {dept} Manager", 5: f"{dept} Director"}.get(level, f"{dept} Manager")
    if role == "Research Director":
        return {3: "Research Director", 4: "Senior Research Director", 5: "Head of Research"}.get(level, "Research Director")
    if role == "Manufacturing Director":
        return role          # already a senior title in IBM's naming: no level prefix
    if role == "Human Resources":
        role = "HR Specialist"
    return f"{config.LEVEL_PREFIX.get(level, '')}{role}"


def _rescale_score(value):
    lo, hi = config.SURVEY_SOURCE_RANGE
    tlo, thi = config.SURVEY_TARGET_RANGE
    return round(tlo + (value - lo) * (thi - tlo) / (hi - lo), 2)


# ---------------------------------------------------------------------------
# 1. Employees (dates, titles, status, exit reasons)
# ---------------------------------------------------------------------------

def exit_reason(row, role_level_median_salary) -> str:
    """Exit reason written from the leaver's own data, strongest signals first."""
    reasons = []
    salary = row["MonthlyIncome"] * 12
    median = role_level_median_salary.get((row["JobRole"], row["JobLevel"]), salary)
    if row["OverTime"] == "Yes" and row["WorkLifeBalance"] <= 2:
        reasons.append("Burnout: regular overtime and a poor work-life balance.")
    elif row["OverTime"] == "Yes":
        reasons.append("Left after long periods of overtime.")
    if salary < 0.85 * median:
        reasons.append("Paid below peers in the same role and level; accepted a better-paid offer.")
    if row["YearsSinceLastPromotion"] >= 4:
        reasons.append(f"No promotion for {row['YearsSinceLastPromotion']} years.")
    if row["JobSatisfaction"] <= 1:
        reasons.append("Low job satisfaction.")
    if row["EnvironmentSatisfaction"] <= 1:
        reasons.append("Unhappy with the work environment.")
    if row["DistanceFromHome"] >= 20:
        reasons.append(f"Long commute ({row['DistanceFromHome']} km).")
    if row["BusinessTravel"] == "Travel_Frequently":
        reasons.append("Too much business travel.")
    if row["NumCompaniesWorked"] >= 5:
        reasons.append(f"Frequent job changer ({row['NumCompaniesWorked']} previous employers).")
    if row["YearsAtCompany"] <= 1:
        reasons.append("Left within the first year.")
    if not reasons:
        reasons.append("Accepted an opportunity at another company.")
    return " ".join(reasons[:2])


def build_employees(src, report, ids: IdentityFactory, rng, snapshot):
    df = src.copy()
    df["salary"] = (df["MonthlyIncome"] * 12).astype(float)
    median_salary = df.groupby(["JobRole", "JobLevel"])["salary"].median().to_dict()

    left = df["Attrition"] == "Yes"
    # Leavers left during the last year; the others are still here on the snapshot day
    end = pd.Series(snapshot, index=df.index)
    end[left] = [snapshot - _days(rng, 15, 365) for _ in range(int(left.sum()))]
    start = [e - pd.DateOffset(years=int(y)) - _days(rng, 0, 330)
             for e, y in zip(end, df["YearsAtCompany"])]
    dob = [snapshot - pd.DateOffset(years=int(a)) - _days(rng, 0, 364) for a in df["Age"]]

    names = [ids.name(g) for g in df["Gender"]]
    out = pd.DataFrame({
        "employee_id": df["EmployeeNumber"].astype(int),
        "first_name": [n[0] for n in names],
        "last_name": [n[1] for n in names],
        "email": [ids.email(f, l) for f, l in names],
        "start_date": pd.to_datetime(start).date,
        "exit_date": [e.date() if is_left else None for e, is_left in zip(end, left)],
        "title": [job_title(r, l, d) for r, l, d in zip(df["JobRole"], df["JobLevel"], df["Department"])],
        "employee_status": np.where(left, "Voluntarily Terminated", "Active"),
        "employee_type": "Full-Time",
        "employee_classification_type": np.where(df["JobLevel"] >= 2, "Exempt", "Non-Exempt"),
        "termination_type": np.where(left, "Voluntary", None),
        "termination_description": [exit_reason(r, median_salary) if l else None
                                    for (_, r), l in zip(df.iterrows(), left)],
        "dob": pd.to_datetime(dob).date,
        "state": None,
        "job_function": df["JobRole"],
        "gender": df["Gender"].str.upper(),
        "location": config.COMPANY_LOCATION,
        "performance_score": df["PerformanceRating"].map(config.PERFORMANCE_LABELS),
        "current_employee_rating": df["PerformanceRating"].astype(float),
        "salary": df["salary"],
        "currency": "USD",
        "needs_review": False,
        "is_deleted": False,
        # detailed IBM attributes (migration V3__employee_attributes.sql)
        "job_level": df["JobLevel"],
        "overtime": df["OverTime"] == "Yes",
        "business_travel": df["BusinessTravel"].map(
            {"Non-Travel": "Non Travel", "Travel_Rarely": "Travel Rarely", "Travel_Frequently": "Travel Frequently"}),
        "distance_from_home": df["DistanceFromHome"],
        "education_level": df["Education"].map(config.EDUCATION_LABELS),
        "education_field": df["EducationField"],
        "total_working_years": df["TotalWorkingYears"],
        "num_companies_worked": df["NumCompaniesWorked"],
        "years_in_current_role": df["YearsInCurrentRole"],
        "years_since_last_promotion": df["YearsSinceLastPromotion"],
        "years_with_curr_manager": df["YearsWithCurrManager"],
        "stock_option_level": df["StockOptionLevel"],
        "percent_salary_hike": df["PercentSalaryHike"],
        "environment_satisfaction": df["EnvironmentSatisfaction"],
        "relationship_satisfaction": df["RelationshipSatisfaction"],
        "training_times_last_year": df["TrainingTimesLastYear"],
        "created_at": _now_str(),
        "updated_at": _now_str(),
    })
    # working columns used by later steps (dropped before loading)
    out["_department"] = df["Department"].values
    out["_role"] = df["JobRole"].values
    out["_end"] = pd.to_datetime(end).values
    out["_years_at_company"] = df["YearsAtCompany"].values

    report.log("employees", "generated_from_ibm", len(out),
               f"{int(left.sum())} leavers (exit in the last 12 months) and {int((~left).sum())} active employees")
    return out


# ---------------------------------------------------------------------------
# 2. Teams (departments table) and manager hierarchy
# ---------------------------------------------------------------------------

def build_teams(emp, report, rng):
    """A 'department' of the app is a team: one job role inside one IBM
    department, split into teams of about TEAM_SIZE people."""
    rows, team_of = [], {}
    dept_id = 0
    for (dept, role), group in emp.groupby(["_department", "_role"], sort=True):
        members = group["employee_id"].to_numpy().copy()
        rng.shuffle(members)
        n_teams = max(1, round(len(members) / config.TEAM_SIZE))
        for k in range(n_teams):
            dept_id += 1
            code = f"{config.DEPARTMENT_CODES[dept]}-{config.ROLE_CODES[role]}-{k + 1}"
            rows.append({
                "department_id": dept_id,
                "business_unit": code,
                "department_type": dept,
                "division_description": f"{_plural(role)} - Team {k + 1}" if n_teams > 1 else _plural(role),
                "is_deleted": False,
                "created_at": _now_str(),
                "_role": role,
            })
            for e in members[k::n_teams]:
                team_of[int(e)] = dept_id
    teams = pd.DataFrame(rows)
    emp["department_id"] = emp["employee_id"].map(team_of).astype(int)
    report.log("departments", "teams_built", len(teams),
               f"{len(teams)} teams from {emp['_department'].nunique()} departments and {emp['_role'].nunique()} job roles")
    return emp, teams


# Who leads the teams of each role
LEADER_ROLE_FOR = {
    "Research Scientist": "Research Director",
    "Laboratory Technician": "Research Director",
    "Manufacturing Director": "Manager",
    "Healthcare Representative": "Manager",
    "Sales Executive": "Manager",
    "Sales Representative": "Manager",
    "Human Resources": "Manager",
}


def assign_managers(emp, teams, report):
    """CEO -> department heads -> leaders -> team members.
    - department head: the active level-5 (else most senior) Manager of the
      department; the CEO is the most senior of the heads
    - each team of a non-leadership role is led by an active level 3-4 leader
      of the same department (Research Directors for research teams,
      Managers otherwise), spread round-robin
    - leaders report to their department head."""
    active = emp["employee_status"] == "Active"
    seniority = emp["job_level"] * 100 + emp["total_working_years"]
    manager = {}

    heads = {}
    for dept, group in emp[active & (emp["_role"] == "Manager")].groupby("_department"):
        heads[dept] = int(group.loc[seniority[group.index].idxmax(), "employee_id"])
    seniority_of = dict(zip(emp["employee_id"], seniority))
    ceo = max(heads.values(), key=lambda e: seniority_of[e])
    for head in heads.values():
        manager[head] = None if head == ceo else ceo

    leaders_by = {}
    pool_mask = active & emp["_role"].isin(config.LEADERSHIP_ROLES) & (emp["job_level"] <= 4)
    for (dept, role), group in emp[pool_mask].groupby(["_department", "_role"]):
        leaders_by[(dept, role)] = list(group.sort_values("total_working_years", ascending=False)["employee_id"])

    team_leader = {}
    cursor = {}
    for _, team in teams.iterrows():
        role = team["_role"]
        if role in config.LEADERSHIP_ROLES:
            continue
        key = (team["department_type"], LEADER_ROLE_FOR[role])
        pool = leaders_by.get(key) or leaders_by.get((team["department_type"], "Manager")) or []
        if pool:
            i = cursor.get(key, 0)
            team_leader[team["department_id"]] = pool[i % len(pool)]
            cursor[key] = i + 1

    for _, row in emp.iterrows():
        e = int(row["employee_id"])
        if e in manager:
            continue
        head = heads.get(row["_department"], ceo)
        if row["_role"] in config.LEADERSHIP_ROLES:
            manager[e] = head
        else:
            manager[e] = team_leader.get(row["department_id"], head)
        if manager[e] == e:
            manager[e] = head

    emp["manager_id"] = pd.array([manager.get(int(e)) for e in emp["employee_id"]], dtype="Int64")
    # the most senior department head runs the company
    emp.loc[emp["employee_id"] == ceo, "title"] = "Chief Executive Officer"
    report.log("employees", "manager_hierarchy", len(emp),
               f"CEO {ceo}, {len(heads)} department heads, {len(team_leader)} teams with a leader")
    return emp, heads, ceo


# ---------------------------------------------------------------------------
# 3. Users and roles
# ---------------------------------------------------------------------------

def build_roles():
    return pd.DataFrame(config.ROLES)


def build_users(emp, heads, report):
    admins = set(heads.values())

    def role_for(row):
        e = int(row["employee_id"])
        if e in admins:
            return config.ROLE_IDS["ROLE_ADMIN"]
        if row["_department"] == "Human Resources" and row["job_level"] >= 2:
            return config.ROLE_IDS["ROLE_HR_MANAGER"]
        if row["_role"] in config.LEADERSHIP_ROLES:
            return config.ROLE_IDS["ROLE_MANAGER"]
        return config.ROLE_IDS["ROLE_EMPLOYEE"]

    now = _now_str()
    users = pd.DataFrame({
        "id": [str(uuid.uuid4()) for _ in range(len(emp))],
        "employee_id": emp["employee_id"].values,
        "email": emp["email"].values,
        "password_hash": config.DEFAULT_PASSWORD_HASH,
        "is_active": (emp["employee_status"] == "Active").values,
        "role_id": emp.apply(role_for, axis=1).values,
        "created_at": now, "updated_at": now,
        "created_by": "SYSTEM_ETL", "updated_by": "SYSTEM_ETL",
    })
    counts = users["role_id"].map({r["id"]: r["name"] for r in config.ROLES}).value_counts().to_dict()
    report.log("users", "generated", len(users), f"One account per employee, roles: {counts}")
    return users


def build_user_tokens():
    # Nobody is waiting to join in this data set (no 'Future Start'), so no activation token.
    return pd.DataFrame(columns=["id", "user_id", "token", "token_type", "expires_at",
                                 "is_used", "is_revoked", "created_at"])


# ---------------------------------------------------------------------------
# 4. Salary history, trainings, surveys
# ---------------------------------------------------------------------------

def build_salary_history(emp, rng, report):
    rows = []
    for _, e in emp.iterrows():
        start = pd.Timestamp(e["start_date"])
        end = pd.Timestamp(e["_end"])
        hike = int(e["percent_salary_hike"])
        if e["_years_at_company"] >= 1:
            previous = round(e["salary"] / (1 + hike / 100), 2)
            rows.append({"employee_id": e["employee_id"], "effective_date": start.date(), "salary": previous,
                         "currency": "USD", "change_reason": "INITIAL_HIRE"})
            review = max(end - _days(rng, 30, 330), start + pd.Timedelta(days=365))
            rows.append({"employee_id": e["employee_id"], "effective_date": min(review, end).date(),
                         "salary": e["salary"], "currency": "USD",
                         "change_reason": f"ANNUAL_REVIEW (+{hike}%)"})
        else:
            rows.append({"employee_id": e["employee_id"], "effective_date": start.date(), "salary": e["salary"],
                         "currency": "USD", "change_reason": "INITIAL_HIRE"})
    history = pd.DataFrame(rows)
    history["created_at"] = _now_str()
    report.log("salary_history", "generated", len(history),
               "Hire salary = current salary before the last raise (IBM PercentSalaryHike), then the annual review")
    return history


def build_trainings(emp, rng, report):
    """Each employee gets as many sessions as IBM's TrainingTimesLastYear, in
    the year before the snapshot (or their exit). The course fits the role."""
    names = list(config.TRAINING_CATALOG)
    course_id = {n: i + 1 for i, n in enumerate(names)}
    sessions = []
    for _, e in emp.iterrows():
        n = int(e["training_times_last_year"])
        if n == 0:
            continue
        options = config.TRAINING_BY_ROLE[e["_role"]]
        weights = np.array([1.0 / (i + 1) for i in range(len(options))])
        end = pd.Timestamp(e["_end"])
        start = max(pd.Timestamp(e["start_date"]), end - pd.Timedelta(days=365))
        span = max(1, (end - start).days)
        for _ in range(n):
            course = options[rng.choice(len(options), p=weights / weights.sum())]
            spec = config.TRAINING_CATALOG[course]
            sessions.append({
                "employee_id": e["employee_id"],
                "course_id": course_id[course],
                "training_date": (start + pd.Timedelta(days=int(rng.integers(0, span)))).date(),
                "completion_status": "Completed" if rng.random() < 0.88 else "Incomplete",
                "location": str(rng.choice(config.TRAINING_LOCATIONS)),
                "cost": round(float(rng.uniform(*spec["cost"])), 2),
                "duration_days": int(rng.integers(spec["days"][0], spec["days"][1] + 1)),
            })
    trainings = pd.DataFrame(sessions)
    medians = trainings.groupby("course_id").agg(cost=("cost", "median"), duration_days=("duration_days", "median"))
    courses = pd.DataFrame([{
        "course_id": course_id[n],
        "program_name": n,
        "training_type": config.TRAINING_CATALOG[n]["type"],
        "trainer": config.TRAINERS[i % len(config.TRAINERS)],
        "duration_days": float(medians.loc[course_id[n], "duration_days"]) if course_id[n] in medians.index else None,
        "cost": round(float(medians.loc[course_id[n], "cost"]), 2) if course_id[n] in medians.index else None,
        "is_active": True,
    } for i, n in enumerate(names)])
    report.log("employee_trainings", "generated", len(trainings),
               "Number of sessions per employee = IBM TrainingTimesLastYear; course / cost / date generated")
    return courses, trainings


def build_surveys(emp, src, rng, report):
    rows = []
    for (_, e), (_, s) in zip(emp.iterrows(), src.iterrows()):
        end = pd.Timestamp(e["_end"])
        date = max(end - _days(rng, 10, 120), pd.Timestamp(e["start_date"]))
        rows.append({
            "employee_id": e["employee_id"],
            "survey_date": date.date(),
            "engagement_score": _rescale_score(s["JobInvolvement"]),
            "satisfaction_score": _rescale_score(s["JobSatisfaction"]),
            "work_life_balance_score": _rescale_score(s["WorkLifeBalance"]),
        })
    report.log("surveys", "generated", len(rows),
               "Engagement = JobInvolvement, satisfaction = JobSatisfaction, work-life = WorkLifeBalance (1-4 rescaled to 1-5)")
    return pd.DataFrame(rows)



# ---------------------------------------------------------------------------
# 4b. Performance reviews and leave requests
# ---------------------------------------------------------------------------

def build_performance_reviews(emp, src, users, rng, snapshot, report):
    """Last annual review of every employee: the rating is IBM's
    PerformanceRating (3 = meets, 4 = exceeds, on a 1-5 scale); the comment
    is written from the employee's own data; the reviewer is their manager."""
    email_of = dict(zip(users["employee_id"], users["email"]))
    rows = []
    for (_, e), (_, s) in zip(emp.iterrows(), src.iterrows()):
        end = pd.Timestamp(e["_end"])
        date = max(end - _days(rng, 30, 300), pd.Timestamp(e["start_date"]) + pd.Timedelta(days=30))
        if date > end:
            continue                     # joined too recently for a review
        rating = int(s["PerformanceRating"])
        notes = ["Exceeds expectations." if rating >= 4 else "Meets expectations."]
        notes.append({4: "Very high involvement.", 3: "Good involvement.",
                      2: "Involvement could improve.", 1: "Low involvement: needs support."}[int(s["JobInvolvement"])])
        if s["TrainingTimesLastYear"] >= 4:
            notes.append(f"Followed {int(s['TrainingTimesLastYear'])} trainings this year.")
        if s["YearsSinceLastPromotion"] >= 4:
            notes.append(f"No promotion for {int(s['YearsSinceLastPromotion'])} years: discuss career path.")
        if s["OverTime"] == "Yes":
            notes.append("Regular overtime: watch the workload.")
        manager = e["manager_id"]
        rows.append({
            "employee_id": e["employee_id"],
            "reviewer": email_of.get(int(manager)) if pd.notna(manager) else None,
            "review_date": date.date(),
            "rating": rating,
            "comments": " ".join(notes),
        })
    report.log("performance_reviews", "generated", len(rows),
               "Rating = IBM PerformanceRating; comment from involvement, trainings, promotions, overtime")
    return pd.DataFrame(rows)


LEAVE_TYPES = {"ANNUAL": 0.72, "SICK": 0.18, "UNPAID": 0.05, "OTHER": 0.05}


def build_leave_requests(emp, users, rng, snapshot, report):
    """GENERATED: 0-3 leave requests per employee over the last year (decided)
    plus some upcoming ones still pending, so the approval page has work."""
    email_of = dict(zip(users["employee_id"], users["email"]))
    types, weights = list(LEAVE_TYPES), np.array(list(LEAVE_TYPES.values()))
    rows = []
    for _, e in emp.iterrows():
        end = pd.Timestamp(e["_end"])
        start_limit = max(pd.Timestamp(e["start_date"]), end - pd.Timedelta(days=365))
        span = (end - start_limit).days
        if span < 20:
            continue
        for _ in range(int(rng.choice([0, 1, 1, 2, 2, 3]))):
            kind = types[rng.choice(len(types), p=weights)]
            length = int(rng.integers(1, 4)) if kind == "SICK" else int(rng.integers(2, 11))
            first = start_limit + pd.Timedelta(days=int(rng.integers(0, max(1, span - length))))
            decided_by = email_of.get(int(e["manager_id"])) if pd.notna(e["manager_id"]) else None
            rows.append({
                "employee_id": e["employee_id"], "leave_type": kind,
                "start_date": first.date(), "end_date": (first + pd.Timedelta(days=length - 1)).date(),
                "reason": None, "status": "APPROVED" if rng.random() < 0.93 else "REJECTED",
                "decided_by": decided_by,
                "decided_at": (first - pd.Timedelta(days=int(rng.integers(3, 20)))).strftime("%Y-%m-%d %H:%M:%S"),
                "created_at": (first - pd.Timedelta(days=int(rng.integers(20, 40)))).strftime("%Y-%m-%d %H:%M:%S"),
            })
        # upcoming leave, not decided yet (active employees only)
        if e["employee_status"] == "Active" and rng.random() < 0.04:
            first = snapshot + pd.Timedelta(days=int(rng.integers(7, 60)))
            length = int(rng.integers(2, 11))
            rows.append({
                "employee_id": e["employee_id"], "leave_type": "ANNUAL",
                "start_date": first.date(), "end_date": (first + pd.Timedelta(days=length - 1)).date(),
                "reason": str(rng.choice(["Family holiday", "Personal matters", "Wedding", "Moving house", None])),
                "status": "PENDING", "decided_by": None, "decided_at": None,
                "created_at": (snapshot - pd.Timedelta(days=int(rng.integers(0, 6)))).strftime("%Y-%m-%d %H:%M:%S"),
            })
    df = pd.DataFrame(rows)
    df["reason"] = df["reason"].replace({"None": None})
    report.log("leave_requests", "generated", len(df),
               f"Generated leave history; {int((df['status'] == 'PENDING').sum())} requests pending approval")
    return df

# ---------------------------------------------------------------------------
# 5. Recruitment: openings where people left, real resumes as applicants
# ---------------------------------------------------------------------------

def posting_description(title, team, department, years) -> str:
    """Short template description (derived from the title's required skills)."""
    skills = skills_for_title(title) or "strong communication, teamwork and problem solving"
    return (
        f"Nexus is hiring a {title} for its {department} department ({team}). "
        f"You will join an experienced team and contribute from day one.\n\n"
        f"Profile:\n"
        f"- About {years} years of relevant experience\n"
        f"- Key skills: {skills}\n"
        f"- Clear communication and a collaborative attitude"
    )


def build_job_postings(emp, teams, rng, snapshot, report):
    active = emp[emp["employee_status"] == "Active"]
    leavers = emp[emp["employee_status"] != "Active"]
    postings = []
    job_id = 0
    for role, group in leavers.groupby("_role"):
        n = max(1, round(len(group) / config.LEAVERS_PER_POSTING))
        # teams of that role, the ones that lost the most people first
        lost = group.groupby("department_id").size().sort_values(ascending=False)
        levels = group["job_level"].value_counts().index.tolist()
        for k in range(n):
            job_id += 1
            team_id = int(lost.index[k % len(lost)])
            dept = teams.loc[teams["department_id"] == team_id, "department_type"].iloc[0]
            level = int(levels[k % len(levels)])
            peers = active[(active["_role"] == role) & (active["job_level"] == level)]
            if peers.empty:
                peers = active[active["_role"] == role]
            low, high = np.percentile(peers["salary"], [25, 75])
            postings.append({
                "job_id": job_id,
                "title": job_title(role, level, dept),
                "department_id": team_id,
                "location": config.COMPANY_LOCATION,
                "required_experience_years": int(np.median(peers["total_working_years"])),
                "offered_salary_min": float(math.floor(low / 500) * 500),
                "offered_salary_max": float(math.ceil(high / 500) * 500),
                "status": "OPEN",
                "created_at": snapshot - _days(rng, 5, config.POSTING_WINDOW_DAYS),
                "_role": role,
            })
    jobs = pd.DataFrame(postings).sort_values("created_at").reset_index(drop=True)
    team_name = dict(zip(teams["department_id"], teams["division_description"]))
    jobs["description"] = [
        posting_description(t, team_name.get(d, ""), dept, x)
        for t, d, dept, x in zip(jobs["title"], jobs["department_id"],
                                 jobs["department_id"].map(dict(zip(teams["department_id"], teams["department_type"]))),
                                 jobs["required_experience_years"])
    ]
    n_filled = int(round(len(jobs) * config.FILLED_POSTING_SHARE))
    jobs.loc[: n_filled - 1, "status"] = "FILLED"          # the oldest ones
    report.log("job_postings", "generated", len(jobs),
               f"One opening per ~{config.LEAVERS_PER_POSTING} leavers of a role ({n_filled} already filled)")
    return jobs


def _weighted_status(rng, weights):
    names = list(weights)
    p = np.array([weights[n] for n in names])
    return names[rng.choice(len(names), p=p / p.sum())]


def build_applications(jobs, resumes, ids: IdentityFactory, rng, snapshot, report):
    """Each opening receives real resumes: most from matching categories,
    some unrelated (a nurse applying to Sales happens; the AI must spot it)."""
    unused = set(resumes.index)
    by_category = {c: list(g.index) for c, g in resumes.groupby("Category")}
    for c in by_category:
        rng.shuffle(by_category[c])

    def take(categories):
        for c in rng.permutation(categories):
            pool = by_category.get(c, [])
            while pool:
                i = pool.pop()
                if i in unused:
                    unused.discard(i)
                    return i
        return None

    applicants, applications, cvs = [], [], []
    applicant_id = 0
    now = _now_str()
    for _, job in jobs.iterrows():
        related = config.RESUME_CATEGORIES_BY_ROLE[job["_role"]]
        unrelated = [c for c in by_category if c not in related]
        n = int(rng.integers(*config.APPLICANTS_PER_POSTING))
        chosen = []
        for _ in range(n):
            want_related = rng.random() < config.RELATED_APPLICANT_SHARE
            i = take(related if want_related else unrelated)
            if i is None:
                i = take(unrelated if want_related else related)
            if i is not None:
                chosen.append((i, resumes.loc[i, "Category"] in related))

        created = pd.Timestamp(job["created_at"])
        window = max(1, min(60, (snapshot - created).days))
        # a filled opening was given to one of the related applicants
        hired = next((k for k, (_, rel) in enumerate(chosen) if rel), None) if job["status"] == "FILLED" else None

        for k, (i, is_related) in enumerate(chosen):
            applicant_id += 1
            first, last = ids.name()
            applied = created + pd.Timedelta(days=int(rng.integers(0, window)))
            if job["status"] == "FILLED":
                status = "OFFERED" if k == hired else "REJECTED"
            elif is_related:
                status = _weighted_status(rng, config.APPLICATION_STATUS_WEIGHTS)
            else:
                status = _weighted_status(rng, {"APPLIED": 0.35, "IN REVIEW": 0.15, "REJECTED": 0.50})
            changed = None
            if status != "APPLIED":
                changed = min(applied + _days(rng, 3, 40), snapshot).strftime("%Y-%m-%d %H:%M:%S")
            low, high = job["offered_salary_min"], job["offered_salary_max"]

            applicants.append({
                "applicant_id": applicant_id,
                "first_name": first, "last_name": last,
                # example.com is reserved for examples: interview / rejection
                # emails sent by the app can never reach a real person
                "email": ids.email(first, last, domain="example.com"),
                "phone_number": ids.phone(),
                "education_level": None, "years_of_experience": None,   # read from the CV by the AI
                "gender": None, "dob": None, "address": None, "city": None,
                "state": None, "zip_code": None, "country": None,
                "created_at": applied.strftime("%Y-%m-%d %H:%M:%S"),
            })
            applications.append({
                "application_id": str(uuid.uuid4()),
                "applicant_id": applicant_id,
                "job_id": int(job["job_id"]),
                "application_date": applied.date(),
                "desired_salary": round(float(rng.uniform(low * 0.9, high * 1.1)) / 100) * 100,
                "status": status,
                "ai_match_score": pd.NA,          # computed later by the AI matcher
                "status_updated_at": changed,
                "created_at": now,
            })
            r = resumes.loc[i]
            cvs.append({
                "id": str(uuid.uuid4()),
                "applicant_id": applicant_id,
                "file_url": (f"{config.MINIO_ENDPOINT.rstrip('/')}/{config.MINIO_BUCKET}/{int(r['ID'])}.pdf"
                             if r["pdf_path"] else None),
                "parsed_text": r["Resume_str"],
                "created_at": now,
                "_pdf_path": r["pdf_path"],
                "_related": is_related,
            })

    applicants = pd.DataFrame(applicants)
    applications = pd.DataFrame(applications)
    applications["ai_match_score"] = applications["ai_match_score"].astype("Int64")
    cvs = pd.DataFrame(cvs)
    report.log("applicants", "generated", len(applicants),
               f"Real resumes; {int(cvs['_related'].sum())} in a related field, {int((~cvs['_related']).sum())} unrelated")
    report.log("job_applications", "generated", len(applications),
               f"Statuses: {applications['status'].value_counts().to_dict()}")
    return applicants, applications, cvs


# ---------------------------------------------------------------------------
# orchestration
# ---------------------------------------------------------------------------

def run_transform(cleaned, report):
    print("TRANSFORM")
    rng = np.random.default_rng(config.SEED)
    ids = IdentityFactory(config.SEED, config.COMPANY_DOMAIN)
    snapshot = snapshot_date()
    print(f"  snapshot date: {snapshot.date()}")

    src = cleaned["employees"]
    emp = build_employees(src, report, ids, rng, snapshot)
    emp, teams = build_teams(emp, report, rng)
    emp, heads, ceo = assign_managers(emp, teams, report)
    users = build_users(emp, heads, report)
    salary_history = build_salary_history(emp, rng, report)
    courses, trainings = build_trainings(emp, rng, report)
    surveys = build_surveys(emp, src, rng, report)
    reviews = build_performance_reviews(emp, src, users, rng, snapshot, report)
    leave = build_leave_requests(emp, users, rng, snapshot, report)
    jobs = build_job_postings(emp, teams, rng, snapshot, report)
    applicants, applications, cvs = build_applications(jobs, cleaned["resumes"], ids, rng, snapshot, report)

    jobs["created_at"] = pd.to_datetime(jobs["created_at"]).dt.strftime("%Y-%m-%d %H:%M:%S")

    def drop_work(df):
        return df[[c for c in df.columns if not c.startswith("_")]]

    return {
        "roles": build_roles(),
        "departments": drop_work(teams),
        "employees": drop_work(emp.drop(columns=["email"])),
        "salary_history": salary_history,
        "users": users,
        "user_tokens": build_user_tokens(),
        "training_courses": courses,
        "employee_trainings": trainings,
        "surveys": surveys,
        "performance_reviews": reviews,
        "leave_requests": leave,
        "applicants": applicants,
        "job_postings": drop_work(jobs),
        "job_applications": applications,
        "applicant_cvs": drop_work(cvs),
        # not loaded: which PDF to upload for which CV (see load.upload_cv_pdfs)
        "_cv_files": cvs.loc[cvs["_pdf_path"].notna(), ["file_url", "_pdf_path"]],
    }
