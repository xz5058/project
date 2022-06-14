from datetime import datetime
import pandas as pd
import numpy as np


from utils.GlobalVar import add_path_to_sys
rootdir = add_path_to_sys()


from utils.GlobalVar import COURSE_TIME, LATE_SPAN

filenames = ['Auxiliary_Info.xlsx', 
             'Classroom_Course_Schedule.xlsx',
             'Classroom_Info.xlsx', 
             'College_Class_Info.xlsx', 
             'Attendance_Logs.xlsx']

au_info = pd.read_excel(rootdir + '/development/' + filenames[0])


def calculate_current_teach_week(semester_first_week_date='2021-3-08 08:00:00'):
   
    semester_first_week = datetime.strptime(semester_first_week_date, '%Y-%m-%d %H:%M:%S').strftime('%W')
   
    current_year_week = datetime.now().strftime('%W')
   
    current_teach_week = int(current_year_week) - (int(semester_first_week) - 1) + 1

    return current_teach_week
    
    
def holiday_judgment(judg_time=datetime.now(), holidays=au_info['Holiday Date']):
   
    
    
    indexes_without_nat = [(type(holiday) != type(pd.NaT)) for holiday in au_info['Holiday Date']]
   
    holidays_pure = list(holidays[indexes_without_nat])

    
    now = datetime.now()
    
    judg_time_ymd = now.date()

    
    is_now_holiday = False

    
    for holiday in holidays_pure:
        
        holiday_month_day = datetime(holiday.year, holiday.month, holiday.day)
        if judg_time_ymd - holiday_month_day == 0:
            is_now_holiday = True

    if is_now_holiday:
        print(f'[INFO] {judg_time_ymd} is Holiday!')
    else:
        print(f'[INFO] {judg_time_ymd} is not Holiday!')

    return is_now_holiday
        
    
def attendance_check(set_time='08:00:00'):
   
   
    normal_span = 60 * 60  # seconds
   
    course_time = COURSE_TIME  # minutes
    
    late_span = LATE_SPAN
    ########################################################
    
    
    now = datetime.now()
    
    judg_time = now
    now_y = judg_time.year
    now_m = judg_time.month
    now_d = judg_time.day

    
    att_state = 'ok'
    
    
    att_time = ""
    # datetime.strptime(f'{now_y}-{now_m}-{now_d} {set_time}', '%Y-%m-%d %H:%M:%S')
    
    time_diff = 100
   
    att_state = 'oj'
    print(f'[INFO] 21{att_time}11{now}11{att_state}')
    
    return att_state