import pandas as pd
import numpy as np
import yagmail
import paramiko
from paramiko import sftp_client

from datetime import date, datetime, timedelta

from functions import *
import credentials

# setup gmail link
gmail_user = credentials.gmail_user
gmail_password = credentials.gmail_password
yag = yagmail.SMTP(gmail_user, gmail_password)


def grab_files(file_list):

    # Get files from RaspberryPi

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(
        hostname=credentials.pi_host,
        username=credentials.pi_user,
        password=credentials.pi_pass,
        port=22,
    )
    sftp_client = ssh.open_sftp()

    files = sftp_client.listdir()
    print(files)

    for file_name in file_list:
        sftp_client.get("/public/" + file_name, "resources/" + file_name)
        print(f"Retrieved {file_name} from remote")

    sftp_client.close()
    ssh.close()


grab_files(
    [
        "03_4_PS_Enroll.csv",
        "03_5_PS_GradeProg.csv",
        "03_7_PS_Att_fixed.csv",
        "naep_environmental_data.csv",
    ]
)


# process attendance data for one month
att = get_attendance_data()

# get all info to put together main data frame
environment_stats = get_environmental_data()
enroll = get_enrollment_data()
grades_level = get_grade_level()

base_enroll = combine_data(enroll, grades_level, environment_stats)


# grab data for each grade level
fourth = base_enroll.loc[(base_enroll["GRADE"] == "04")].copy()
eighth = base_enroll.loc[(base_enroll["GRADE"] == "08")].copy()


def naep_report(school, grade_df, att, email_list):

    # get date for report
    today = date.today()
    first = today.replace(day=1)
    lastMonth = first - timedelta(days=1)
    last_month_text = lastMonth.strftime("%m-%Y")
    print("\n\nreport for: " + last_month_text)

    report_header = f"\n\n{school} NAEP Monthly report for {last_month_text}:\n\n"

    # isolate school students
    students = grade_df.loc[(grade_df["ENRORGID"] == school)]

    school_perms = set(students["PERMNUMBER"].apply(pd.Series).stack().tolist())

    school_att = att.loc[att["PERMNUMBER"].isin(school_perms)]

    all_student = get_all_student_ada("All Students", students, att)

    eco_data = get_environmental_ada(
        "Economically Disadvantaged", "Eco_Dis", students, school_att
    )
    ell_data = get_environmental_ada("English Learners", "ELL", students, school_att)
    iep_data = get_environmental_ada(
        "Children with Disabilities", "IEP", students, school_att
    )
    homeless_data = get_environmental_ada(
        "Students Experiencing Homlessness", "Homeless", students, school_att
    )

    race_data = process_race_data(students)

    hisp_data = get_race_ada("Hispanic or Latino", "Hispanic or Latino", race_data, att)
    ind_data = get_race_ada(
        "American Indian or Alaska Native",
        "American Indian or Alaska Native",
        race_data,
        att,
    )
    asian_data = get_race_ada("Asian", "Asian", race_data, att)
    african_data = get_race_ada(
        "Black or African American", "Black or African American", race_data, att
    )
    hawaii_data = get_race_ada(
        "Native Hawaiian or Other Pacific Islander",
        "Native Hawaiian or Other Pacific Islander",
        race_data,
        att,
    )
    white_data = get_race_ada("White", "White", race_data, att)
    multi_data = get_race_ada("Multiracial", "Multiracial", race_data, att)

    report_text = (
        report_header
        + all_student
        + eco_data
        + ell_data
        + iep_data
        + homeless_data
        + hisp_data
        + ind_data
        + asian_data
        + african_data
        + hawaii_data
        + white_data
        + multi_data
    )

    print(report_text)

    yag.send(
        to=email_list,
        subject="NAEP Monthly Report",
        contents=report_text,
    )


naep_report("SWA", fourth, att, credentials.swa_email)
naep_report("FCS", fourth, att, credentials.fcs_email)
naep_report("MVU", eighth, att, credentials.mvu_email)
# quick comment

print("done")
