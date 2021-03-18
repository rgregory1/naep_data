import pandas as pd
import numpy as np

from datetime import date


def get_attendance_data():

    # read attendance data
    df_att = pd.read_csv(
        "resources/03_7_PS_Att_fixed.csv", dtype=str, parse_dates=["ATTEVENTDATE"]
    )

    df_att["ENRORGID"].replace("PS115", "FCS", inplace=True)
    df_att["ENRORGID"].replace("PS142", "HES", inplace=True)
    df_att["ENRORGID"].replace("PS187", "MVU", inplace=True)
    df_att["ENRORGID"].replace("PS295", "SWA", inplace=True)

    # find past month
    current_date = date.today()
    last_month = current_date.month - 1
    # print("Last month: " + str(last_month))

    # create new df with only att data in past month
    att = df_att.loc[df_att["ATTEVENTDATE"].dt.month == last_month]
    # print(att.head())

    # drop all non-essential columns from PS_Enroll file
    att = att.iloc[:, [1, 2, 3, 4]].copy()
    return att


def get_environmental_data():
    # read in student environmental data
    df_raw_stats = pd.read_csv(
        "resources/naep_environmental_data.csv", header=None, dtype=str
    )
    df_raw_stats.rename(
        columns={
            0: "PERMNUMBER",
            1: "Eco_Dis",
            2: "ELL",
            3: "IEP",
            4: "Homeless",
            5: "Track",
        },
        inplace=True,
    )
    # print(df_raw_stats.head())
    # clean up environmental data
    df_raw_stats["Eco_Dis"].replace("01", "Y", inplace=True)
    df_raw_stats["Eco_Dis"].replace("02", "Y", inplace=True)
    df_raw_stats["Eco_Dis"].replace("96", "N", inplace=True)
    df_raw_stats["Eco_Dis"] = df_raw_stats["Eco_Dis"].fillna("N")

    df_raw_stats["ELL"] = df_raw_stats["ELL"].fillna("N")

    df_raw_stats["IEP"] = df_raw_stats["IEP"].fillna("N")

    df_raw_stats["Homeless"] = df_raw_stats["Homeless"].fillna("N")

    return df_raw_stats


def get_enrollment_data():
    # get enrollment data
    df_raw_enroll = pd.read_csv("resources/03_4_PS_Enroll.csv", dtype=str)

    df_raw_enroll["ENRORGID"].replace("PS115", "FCS", inplace=True)
    df_raw_enroll["ENRORGID"].replace("PS142", "HES", inplace=True)
    df_raw_enroll["ENRORGID"].replace("PS187", "MVU", inplace=True)
    df_raw_enroll["ENRORGID"].replace("PS295", "SWA", inplace=True)

    # drop all non-essential columns from PS_Enroll file
    df_enroll = df_raw_enroll.iloc[:, [1, 2, 3, 4, 5, 6, 7, 8, 12, 17]].copy()

    # drop students that are no longer enrolled
    df_enroll = df_enroll.loc[df_enroll["ENRENDDATE"].isnull()]

    return df_enroll


def get_grade_level():
    # read in gradprog
    df_grades = pd.read_csv("resources/03_5_PS_GradeProg.csv", dtype=str)

    # drop all non-essential columns from PS_Enroll file
    df_grades = df_grades.iloc[:, [2, 3]].copy()

    return df_grades


def combine_data(enroll, grades_level, environment_stats):
    # combine df's into one df
    sub_enroll = pd.merge(enroll, grades_level, how="left", on=["PERMNUMBER"])

    # remove the unused column
    sub_enroll = sub_enroll.drop("ENRENDDATE", 1)

    # remove EEE students from enrollment file
    sub_enroll = sub_enroll[~sub_enroll["GRADE"].isin(["EE"])]

    # add subpopulation data
    enroll = pd.merge(sub_enroll, environment_stats, how="left", on=["PERMNUMBER"])
    # print(enroll.head())

    return enroll


def process_race_data(df_enroll_begin):

    df_enroll = df_enroll_begin.copy()
    # make all Y and N into numbers for calculation
    df_enroll["ETHNO"].replace("2", 0, inplace=True)
    df_enroll["RACE_AMI"].replace("Y", 1, inplace=True)
    df_enroll["RACE_AMI"].replace("N", 0, inplace=True)
    df_enroll["RACE_ASI"].replace("Y", 1, inplace=True)
    df_enroll["RACE_ASI"].replace("N", 0, inplace=True)
    df_enroll["RACE_AFA"].replace("Y", 1, inplace=True)
    df_enroll["RACE_AFA"].replace("N", 0, inplace=True)
    df_enroll["RACE_NAT"].replace("Y", 1, inplace=True)
    df_enroll["RACE_NAT"].replace("N", 0, inplace=True)
    df_enroll["RACE_WHT"].replace("Y", 1, inplace=True)
    df_enroll["RACE_WHT"].replace("N", 0, inplace=True)

    # make sure all these columns are ints
    df_enroll["ETHNO"] = df_enroll["ETHNO"].astype(int)
    df_enroll["RACE_AMI"] = df_enroll["RACE_AMI"].astype(int)
    df_enroll["RACE_ASI"] = df_enroll["RACE_ASI"].astype(int)
    df_enroll["RACE_AFA"] = df_enroll["RACE_AFA"].astype(int)
    df_enroll["RACE_NAT"] = df_enroll["RACE_NAT"].astype(int)
    df_enroll["RACE_WHT"] = df_enroll["RACE_WHT"].astype(int)

    # new column adding all racial 1's to determine df_enroll racial
    df_enroll["multi"] = df_enroll.apply(
        lambda row: row.RACE_AMI
        + row.RACE_ASI
        + row.RACE_AFA
        + row.RACE_NAT
        + row.RACE_WHT,
        axis=1,
    )
    # df_enroll.head()

    # check if multi racial, then remove race date from idividual race columns
    df_enroll.loc[
        df_enroll.multi > 1,
        ["RACE_AMI", "RACE_ASI", "RACE_AFA", "RACE_NAT", "RACE_WHT"],
    ] = (0, 0, 0, 0, 0)

    # check if hispanic, then remove race date from individual race columns
    df_enroll.loc[
        df_enroll.ETHNO == 1,
        ["RACE_AMI", "RACE_ASI", "RACE_AFA", "RACE_NAT", "RACE_WHT", "multi"],
    ] = (0, 0, 0, 0, 0, 0)

    # if multi column is one, replace with zero allowing single race colomn to
    # be the only one holding a value
    df_enroll["multi"].replace(1, 0, inplace=True)

    # reset multi racial values to a 1 for a positive
    df_enroll.loc[df_enroll.multi > 1, "multi"] = 1
    # print(df_enroll.head(20))

    new_multi = df_enroll.iloc[:, [0, 1, 2, 3, 4, 5, 6, 7, 14, 15]].copy()

    new_multi.rename(
        columns={
            "ETHNO": "Hispanic or Latino",
            "RACE_AMI": "American Indian or Alaska Native",
            "RACE_ASI": "Asian",
            "RACE_AFA": "Black or African American",
            "RACE_NAT": "Native Hawaiian or Other Pacific Islander",
            "RACE_WHT": "White",
            "multi": "Multiracial",
        },
        inplace=True,
    )

    return new_multi


def get_ada_percentage(df):
    # find total number of ABS and PRS
    s = df.groupby("DAILY_STATUS").apply(len)

    # function to find ADA given df that groups ABS and PRS
    def get_ada_percentage(s):
        # return round((s.PRS / s.sum()) * 100, 2)

        try:
            return round((s.PRS / s.sum()) * 100, 2)
        except:
            return "0%"

    ada_percentage = get_ada_percentage(s)

    return ada_percentage


def get_environmental_ada(factor_printable_name, factor, school_df, df_att):

    # get df of all students that meet certain factor
    factor_df = school_df.loc[(school_df[factor] == "Y")]

    # create remote student df
    remote_df = factor_df.loc[(factor_df["Track"] == "E")]
    #     return remote_df

    if not remote_df.empty:
        remote_list = set(remote_df["PERMNUMBER"].apply(pd.Series).stack().tolist())

        remote_att = df_att.loc[df_att["PERMNUMBER"].isin(remote_list)]

        remote = get_ada_percentage(remote_att)
        #     remote_att.to_csv(r"../remote_report.csv", index=False, header=True)
    else:
        remote = "No remote " + factor_printable_name

    # create in person student df
    in_person_df = factor_df.loc[~(factor_df["Track"] == "E")]

    if not in_person_df.empty:

        in_person_list = set(
            in_person_df["PERMNUMBER"].apply(pd.Series).stack().tolist()
        )

        in_person_att = df_att.loc[df_att["PERMNUMBER"].isin(in_person_list)]

        in_person = get_ada_percentage(in_person_att)

    else:
        in_person = "No in person " + factor_printable_name

    # print(factor_printable_name)
    # print("Remote: " + str(remote))
    # print("In Person: " + str(in_person) + "\n\n")

    return f"""\n {factor_printable_name} \n
    ADA
    Remote: {str(remote)}
    Hybrid: {str(in_person)}
    
    Enrollment
    Total: {len(factor_df)}
    Remote: {len(remote_df)}
    Other: {len(in_person_df)}
    
    ----------------------------------\n"""


def get_race_ada(factor_printable_name, factor, school_df, df_att):

    # get df of all students that meet certain factor
    factor_df = school_df.loc[(school_df[factor] == 1)]

    # create remote student df
    remote_df = factor_df.loc[(factor_df["Track"] == "E")]
    #     return remote_df

    if not remote_df.empty:
        remote_list = set(remote_df["PERMNUMBER"].apply(pd.Series).stack().tolist())

        remote_att = df_att.loc[df_att["PERMNUMBER"].isin(remote_list)]

        remote = get_ada_percentage(remote_att)
        #     remote_att.to_csv(r"../remote_report.csv", index=False, header=True)
    else:
        remote = "No remote " + factor_printable_name

    # create in person student df
    in_person_df = factor_df.loc[~(factor_df["Track"] == "E")]

    if not in_person_df.empty:

        in_person_list = set(
            in_person_df["PERMNUMBER"].apply(pd.Series).stack().tolist()
        )

        in_person_att = df_att.loc[df_att["PERMNUMBER"].isin(in_person_list)]

        in_person = get_ada_percentage(in_person_att)

    else:
        in_person = "No in person " + factor_printable_name

    # print(factor_printable_name)
    # print("Remote: " + str(remote))
    # print("In Person: " + str(in_person) + "\n\n")

    return f"""\n {factor_printable_name} \n
    ADA
    Remote: {str(remote)}
    Hybrid: {str(in_person)}
    
    Enrollment
    Total: {len(factor_df)}
    Remote: {len(remote_df)}
    Other: {len(in_person_df)}
    
    ----------------------------------\n"""


def get_all_student_ada(factor_printable_name, school_df, df_att):

    # create remote student df
    remote_df = school_df.loc[(school_df["Track"] == "E")]
    #     return remote_df

    if not remote_df.empty:
        remote_list = set(remote_df["PERMNUMBER"].apply(pd.Series).stack().tolist())

        remote_att = df_att.loc[df_att["PERMNUMBER"].isin(remote_list)]

        remote = get_ada_percentage(remote_att)
        #     remote_att.to_csv(r"../remote_report.csv", index=False, header=True)
    else:
        remote = "No remote " + factor_printable_name

    # create in person student df
    in_person_df = school_df.loc[~(school_df["Track"] == "E")]

    if not in_person_df.empty:

        in_person_list = set(
            in_person_df["PERMNUMBER"].apply(pd.Series).stack().tolist()
        )

        in_person_att = df_att.loc[df_att["PERMNUMBER"].isin(in_person_list)]

        in_person = get_ada_percentage(in_person_att)

    else:
        in_person = "No in person " + factor_printable_name

    # print(factor_printable_name)
    # print("Remote: " + str(remote))
    # print("In Person: " + str(in_person) + "\n\n")

    return f"""\n {factor_printable_name} \n
    ADA
    Remote: {str(remote)}
    Hybrid: {str(in_person)}
    
    Enrollment
    Total: {len(school_df)}
    Remote: {len(remote_df)}
    Other: {len(in_person_df)}
    
    ----------------------------------\n"""
