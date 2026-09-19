"""
Not part of the pipeline -- just builds fake dirty CSVs so we can prove the
pipeline actually runs and fixes what it claims to. Delete this file (and
sample_data/) once you drop in your real Kaggle CSVs.
"""

import pandas as pd

employees = pd.DataFrame([
    # normal, clean row
    {"Employee ID": "E001", "First Name": "Ahmed", "Last Name": "Ben Ali", "Start Date": "2019-03-01",
     "Exit Date": "", "Title": "Software Engineer", "Supervisor": "Sara Trabelsi", "Email": "ahmed.benali@x.com",
     "Business Unit": "Tech", "Employee Status": "Active", "Employee Type": "Full-Time", "Pay Zone": "Zone1",
     "Employee Classification Type": "Exempt", "Termination Type": "", "Termination Description": "",
     "Department Type": "Engineering", "Division Description": "Product", "DOB": "1995-05-10", "State": "Bizerte",
     "Job Function": "Backend", "Gender": "M", "Location": "TN01", "Race (or) Ethnicity": "N/A",
     "Marital Status": "Single", "Performance Score": "Good", "Current Employee Rating": 4},

    # THE bug the user called out: Active but exit date already passed
    {"Employee ID": "E002", "First Name": "Sara", "Last Name": "Trabelsi", "Start Date": "2015-01-15",
     "Exit Date": "2022-06-30", "Title": "Engineering Manager", "Supervisor": "", "Email": "sara.trabelsi@x.com",
     "Business Unit": "Tech", "Employee Status": "Active", "Employee Type": "Full-Time", "Pay Zone": "Zone1",
     "Employee Classification Type": "Exempt", "Termination Type": "", "Termination Description": "",
     "Department Type": "Engineering", "Division Description": "Product", "DOB": "1988-02-20", "State": "Bizerte",
     "Job Function": "Management", "Gender": "F", "Location": "TN01", "Race (or) Ethnicity": "N/A",
     "Marital Status": "Married", "Performance Score": "Excellent", "Current Employee Rating": 5},

    # missing email, missing rating (bad type), whitespace padding, lowercase status
    {"Employee ID": "E003", "First Name": " Youssef ", "Last Name": " Gharbi ", "Start Date": "2021-09-01",
     "Exit Date": "", "Title": "HR Assistant", "Supervisor": "Ahmed Ben Ali", "Email": "",
     "Business Unit": "HR", "Employee Status": "active", "Employee Type": "Full-Time", "Pay Zone": "Zone2",
     "Employee Classification Type": "Non-Exempt", "Termination Type": "", "Termination Description": "",
     "Department Type": "People", "Division Description": "", "DOB": "1999-01-01", "State": "Tunis",
     "Job Function": "HR", "Gender": "m", "Location": "TN02", "Race (or) Ethnicity": "N/A",
     "Marital Status": "Single", "Performance Score": "Good", "Current Employee Rating": "not_a_number"},

    # duplicate id of E001 -- should be dropped
    {"Employee ID": "E001", "First Name": "Ahmed", "Last Name": "Ben Ali", "Start Date": "2019-03-01",
     "Exit Date": "", "Title": "Software Engineer", "Supervisor": "Sara Trabelsi", "Email": "ahmed.benali@x.com",
     "Business Unit": "Tech", "Employee Status": "Active", "Employee Type": "Full-Time", "Pay Zone": "Zone1",
     "Employee Classification Type": "Exempt", "Termination Type": "", "Termination Description": "",
     "Department Type": "Engineering", "Division Description": "Product", "DOB": "1995-05-10", "State": "Bizerte",
     "Job Function": "Backend", "Gender": "M", "Location": "TN01", "Race (or) Ethnicity": "N/A",
     "Marital Status": "Single", "Performance Score": "Good", "Current Employee Rating": 4},

    # terminated but exit_date missing -- flag, don't guess
    {"Employee ID": "E005", "First Name": "Mona", "Last Name": "Jendoubi", "Start Date": "2018-04-01",
     "Exit Date": "", "Title": "Sales Rep", "Supervisor": "", "Email": "mona.j@x.com",
     "Business Unit": "Sales", "Employee Status": "Terminated", "Employee Type": "Full-Time", "Pay Zone": "Zone1",
     "Employee Classification Type": "Exempt", "Termination Type": "Resignation", "Termination Description": "left",
     "Department Type": "Sales", "Division Description": "Commercial", "DOB": "1990-07-01", "State": "Sfax",
     "Job Function": "Sales", "Gender": "F", "Location": "TN03", "Race (or) Ethnicity": "N/A",
     "Marital Status": "Divorced", "Performance Score": "Average", "Current Employee Rating": 3},

    # exit_date before start_date -- impossible
    {"Employee ID": "E006", "First Name": "Karim", "Last Name": "Sassi", "Start Date": "2020-01-01",
     "Exit Date": "2019-01-01", "Title": "Analyst", "Supervisor": "Sara Trabelsi", "Email": "karim.sassi@x.com",
     "Business Unit": "Tech", "Employee Status": "Terminated", "Employee Type": "Full-Time", "Pay Zone": "Zone1",
     "Employee Classification Type": "Exempt", "Termination Type": "Layoff", "Termination Description": "",
     "Department Type": "Engineering", "Division Description": "Product", "DOB": "1993-03-03", "State": "Bizerte",
     "Job Function": "Data", "Gender": "M", "Location": "TN01", "Race (or) Ethnicity": "N/A",
     "Marital Status": "Single", "Performance Score": "Good", "Current Employee Rating": 4},

    # rating way out of range, bad date string, DOB missing -> underage check skipped safely
    {"Employee ID": "E007", "First Name": "Nadia", "Last Name": "Chaabane", "Start Date": "not-a-date",
     "Exit Date": "", "Title": "Intern", "Supervisor": "Ahmed Ben Ali", "Email": "bad-email-format",
     "Business Unit": "Tech", "Employee Status": "Active", "Employee Type": "Intern", "Pay Zone": "Zone3",
     "Employee Classification Type": "Non-Exempt", "Termination Type": "", "Termination Description": "",
     "Department Type": "Engineering", "Division Description": "Product", "DOB": "", "State": "Bizerte",
     "Job Function": "QA", "Gender": "F", "Location": "TN01", "Race (or) Ethnicity": "N/A",
     "Marital Status": "Single", "Performance Score": "Good", "Current Employee Rating": 99,

     },

    # missing employee id entirely -- should be dropped
    {"Employee ID": "", "First Name": "Ghost", "Last Name": "Row", "Start Date": "2020-01-01",
     "Exit Date": "", "Title": "Nobody", "Supervisor": "", "Email": "ghost@x.com",
     "Business Unit": "Tech", "Employee Status": "Active", "Employee Type": "Full-Time", "Pay Zone": "Zone1",
     "Employee Classification Type": "Exempt", "Termination Type": "", "Termination Description": "",
     "Department Type": "Engineering", "Division Description": "Product", "DOB": "1990-01-01", "State": "Bizerte",
     "Job Function": "Backend", "Gender": "M", "Location": "TN01", "Race (or) Ethnicity": "N/A",
     "Marital Status": "Single", "Performance Score": "Good", "Current Employee Rating": 3},
])

trainings = pd.DataFrame([
    {"Employee ID": "E001", "Training Date": "2022-01-10", "Training Program Name": "Python Basics",
     "Training Type": "Technical", "Training Outcome": "Completed", "Location": "Online", "Trainer": "Coursera",
     "Training Duration (Days)": 3, "Training Cost": 100},
    # negative cost/duration -- bad type
    {"Employee ID": "E002", "Training Date": "2022-05-10", "Training Program Name": "Leadership",
     "Training Type": "Soft Skills", "Training Outcome": "Completed", "Location": "Onsite", "Trainer": "Internal",
     "Training Duration (Days)": -2, "Training Cost": -50},
    # orphan employee id -- should be dropped
    {"Employee ID": "E999", "Training Date": "2022-05-10", "Training Program Name": "Ghost Training",
     "Training Type": "Technical", "Training Outcome": "Completed", "Location": "Online", "Trainer": "Nobody",
     "Training Duration (Days)": 1, "Training Cost": 10},
])

recruitment = pd.DataFrame([
    {"Applicant ID": "A001", "Application Date": "2023-01-05", "First Name": "Wael", "Last Name": "Mejri",
     "Gender": "M", "Date of Birth": "1997-04-01", "Phone Number": "12345678", "Email": "wael@x.com",
     "Address": "12 Rue X", "City": "Bizerte", "State": "Bizerte", "Zip Code": "7000", "Country": "Tunisia",
     "Education Level": "Master", "Years of Experience": 3, "Desired Salary": 1500, "Job Title": "Data Analyst",
     "Status": "Submitted"},
    # negative experience, absurd desired salary as string
    {"Applicant ID": "A002", "Application Date": "2023-02-01", "First Name": "Rim", "Last Name": "Ayari",
     "Gender": "F", "Date of Birth": "2000-09-09", "Phone Number": "87654321", "Email": "rim@x.com",
     "Address": "3 Rue Y", "City": "Tunis", "State": "Tunis", "Zip Code": "1000", "Country": "Tunisia",
     "Education Level": "Bachelor", "Years of Experience": -1, "Desired Salary": "not_a_number", "Job Title": "Recruiter",
     "Status": "under review"},
])

surveys = pd.DataFrame([
    {"Employee ID": "E001", "Survey Date": "2023-06-01", "Engagement Score": 4, "Satisfaction Score": 5,
     "Work-Life Balance Score": 3},
    # score out of 1-5 range -- should clip
    {"Employee ID": "E002", "Survey Date": "2023-06-01", "Engagement Score": 9, "Satisfaction Score": -1,
     "Work-Life Balance Score": 4},
    # orphan employee id -- should be dropped
    {"Employee ID": "E999", "Survey Date": "2023-06-01", "Engagement Score": 3, "Satisfaction Score": 3,
     "Work-Life Balance Score": 3},
])

employees.to_csv("sample_data/Employee_Data.csv", index=False)
trainings.to_csv("sample_data/Training_and_Development_Data.csv", index=False)
recruitment.to_csv("sample_data/Recruitment_Data.csv", index=False)
surveys.to_csv("sample_data/Employee_Engagement_Survey_Data.csv", index=False)
print("Sample dirty data generated in sample_data/")
