from datetime import datetime

import gitlab
import re
from datetime import timedelta
import configparser as cfg
from os import path

file_dir = path.dirname(path.abspath(__file__))

if not path.exists(f"{file_dir}/config.ini"):
    print("config.ini not found!")
    exit(1)

config = cfg.ConfigParser()
config.read(f"{file_dir}/config.ini")


def process_sprint(sprint, per_sprint_time_tracking, overall_time_tracking):
    """
    Processes a sprint object, first processes all issues found in it to calculate the time spent per user.

    :param sprint:                      The sprint object to process
    :param per_sprint_time_tracking:    The per_sprint_time_tracking dictionary, used to keep track of time per user per sprint
    :param overall_time_tracking:       The overall time tracking, used to keep track of users overall time spent
    :return:
    """
    sprint_issues = sprint.issues(all=True)
    user_time_track = {}
    for issue in sprint_issues:
        process_issue(issue, user_time_track)
    # Add the sprint to the per_sprint_time_tracking dictionary, where the value is the breakdown of time per user
    if sprint not in per_sprint_time_tracking:
        per_sprint_time_tracking[sprint] = user_time_track
    # Add on the times spent by people to their overall time
    for key, value in user_time_track.items():
        if key not in overall_time_tracking:
            overall_time_tracking[key] = 0
        overall_time_tracking[key] += value


def process_issue(issue, per_sprint_time_tracking):
    """
    Processes an issue
    """
    per_discussion_time_tracking = {}
    discussions = issue.discussions.list(all=True)
    for discussion in discussions:
        process_discussion(discussion, per_discussion_time_tracking)
    for key, value in per_discussion_time_tracking.items():
        if key not in per_sprint_time_tracking:
            per_sprint_time_tracking[key] = 0
        per_sprint_time_tracking[key] += value


def process_discussion(discussion, per_sprint_time_tracking):
    """
    Processes a discussion, filters out everything except for time added notes.
    """
    notes = list(filter(lambda _note: time_tracking_pattern.match(_note['body']) or
                                      time_removing_pattern.match(_note['body']), discussion.attributes['notes']))
    for note in notes:
        process_note(note, per_sprint_time_tracking)



def process_note(note, per_sprint_time_tracking):
    """
    Processes a note
    """
    user = note['author']['name'].split(' ')[-1]
    if time_removing_pattern.match(note['body']):
        if user in per_sprint_time_tracking:
            per_sprint_time_tracking[user] = 0
    else:
        captures = re.search(time_tracking_pattern, note['body'])
        # Check that user exists in the dictionary, if not then add them
        if user not in per_sprint_time_tracking:
            per_sprint_time_tracking[user] = 0

        # Calculate amount of time added
        if 'm' in captures.group(2):
            per_sprint_time_tracking[user] += int(captures.group(1))
        else:
            per_sprint_time_tracking[user] += int(captures.group(1)) * 60

        if captures.group(4) is not None:
            per_sprint_time_tracking[user] += int(captures.group(4))


def print_time_tracking_per_sprint(per_sprint_time_tracking):
    print("## Per Sprint Breakdown")
    for sprint, time in per_sprint_time_tracking.items():
        if len(time) == 0:
            continue
        print("### " + sprint.title)
        print("| User | Time Spent  |")
        print("|-----|---|")
        for key, value in time.items():
            print("|" + key + "|" + str(timedelta(minutes=int(value)))[:-3] + " hours" + "|")


def print_overall_time_tracking(overall_time_tracking):
    print("## Overall Breakdown")
    print("| User | Time Spent  |")
    print("|-----|---|")
    for key, value in overall_time_tracking.items():
        print("|" + key + "|" + str(timedelta(minutes=int(value)))[:-3] + " hours" + "|")


def process_lab_session_times(group_lab_wiki, sprint_time_tracking, overall_time_tracking):
    lab_tables = re.findall(group_lab_time_table_pattern, group_lab_wiki.content)
    for table in lab_tables:
        process_table(table, sprint_time_tracking, overall_time_tracking)


def get_sprint_from_date(date):
    for sprint in sprints:
        start_date = sprint.attributes['start_date'].split('-')
        start_date = (int(start_date[1]), int(start_date[2]))
        end_date = sprint.attributes['due_date'].split('-')
        end_date = (int(end_date[1]), int(end_date[2]))

        # https://stackoverflow.com/questions/5464410/how-to-tell-if-a-date-is-between-two-other-dates-in-python/5464467
        if start_date <= date < end_date:
            return sprint

    return None


def get_time_from_string(date_string):
    try:
        timestamp = datetime.strptime(date_string, '%I:%M%p')
    except ValueError:
        timestamp = datetime.strptime(date_string, '%I%p')
    return timestamp


def process_table(table, sprint_time_tracking, overall_time_tracking):
    rows = re.findall(table_row_pattern, table)
    for row in rows:
        date = row[0].split('/')
        date = (int(date[1]), int(date[0]))
        sprint = get_sprint_from_date(date)
        if sprint is not None:
            # https://stackoverflow.com/questions/3096953/how-to-calculate-the-time-interval-between-two-time-strings
            start_time = get_time_from_string(row[4])
            end_time = get_time_from_string(row[8])
            # Get total time spent, turn into seconds
            minutes_spent = (end_time - start_time).seconds / 60
            # Add time onto the tracking maps - row[3] is lastname
            add_entry(row[3], minutes_spent, overall_time_tracking, sprint_time_tracking[sprint])


def add_entry(key, value, overall_time_tracking, per_sprint_time_tracking):
    if key not in overall_time_tracking:
        overall_time_tracking[key] = 0
    if key not in per_sprint_time_tracking:
        per_sprint_time_tracking[key] = 0
    overall_time_tracking[key] += value
    per_sprint_time_tracking[key] += value


time_tracking_pattern = re.compile('added (\d+)([h|m])( (\d+)m)?')
time_removing_pattern = re.compile('removed time spent')
group_lab_time_table_pattern = re.compile('#{4} Group Lab Session \d+(?:.+)?(?:\n\|(?:[^|]+\|){5})+')
table_row_pattern = re.compile(
    '\|\s+(\d+\/\d+\/\d+)\s+\|\s*\w+\s*\|\s*((\w+) (\w+))\s*\|\s*((\d+(.\d+)?)(pm|am))\s*\|\s*((\d+(.\d+)?)(pm|am))\s*\|')

gl = gitlab.Gitlab(config['AUTHENTICATION']['GitLabServer'],
                   private_token=config['AUTHENTICATION']['PersonalAccessToken'])

project = gl.projects.get(config['PROJECT']['ID'])

milestones = project.milestones.list()

per_sprint_time_tracking = {}
over_all_time_tracking = {}

sprints = list(filter(lambda milestone: config['PROJECT']['SprintMilestonePrefix'] in milestone.title, milestones))

for sprint in sprints:
    process_sprint(sprint, per_sprint_time_tracking, over_all_time_tracking)

if 'LabTimeWikiSlug' in config['PROJECT']:
    process_lab_session_times(project.wikis.get(config['PROJECT']['LabTimeWikiSlug']), per_sprint_time_tracking,
                              over_all_time_tracking)

print("# Break down for time spent per person")
print_time_tracking_per_sprint(per_sprint_time_tracking)
print_overall_time_tracking(over_all_time_tracking)
