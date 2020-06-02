import gitlab
import re
from datetime import timedelta
import configparser as cfg
from os import path

if not path.exists('config.ini'):
    print("config.ini not found!")
    exit(1)

config = cfg.ConfigParser()
config.read('config.ini')


def process_sprint(sprint, time_tracking):
    print("***********" + sprint.title + "***********")
    sprint_issues = sprint.issues(all=True)
    print(str(len(sprint_issues)) + " issues found")
    user_time_track = {}
    for issue in sprint_issues:
        process_issue(issue, user_time_track)
    print("Break down for " + sprint.title)
    for key, value in user_time_track.items():
        if key not in time_tracking:
            time_tracking[key] = 0
        time_tracking[key] += value
        print('{}{}'.format(key.ljust(30), str(timedelta(minutes=int(value)))[:-3] + " hours"))


def process_issue(issue, user_time_track):
    discussions = issue.discussions.list(all=True)
    for discussion in discussions:
        process_discussion(discussion, user_time_track)


def process_discussion(discussion, user_time_tracking):
    notes = list(filter(lambda _note: time_tracking_pattern.match(_note['body']), discussion.attributes['notes']))
    for note in notes:
        process_note(note, user_time_tracking)


def process_note(note, user_time_tracking):
    captures = re.search(time_tracking_pattern, note['body'])
    user = note['author']['name']
    if user not in user_time_tracking:
        user_time_tracking[user] = 0

    if 'm' in captures.group(2):
        user_time_tracking[user] += int(captures.group(1))
    else:
        user_time_tracking[user] += int(captures.group(1)) * 60

    if captures.group(4) is not None:
        user_time_tracking[user] += int(captures.group(4))


def print_time_tracking(time_tracking):
    for key, value in time_tracking.items():
        print('{}{}'.format(key.ljust(30), str(timedelta(minutes=int(value)))[:-3] + " hours"))


time_tracking_pattern = re.compile('added (\d+)([h|m])( (\d+)m)?')

gl = gitlab.Gitlab(config['AUTHENTICATION']['GitLabServer'],
                   private_token=config['AUTHENTICATION']['PrivateAccessToken'])

project = gl.projects.get(config['PROJECT']['ID'])

milestones = project.milestones.list()

time_tracking = {}

sprints = list(filter(lambda milestone: config['PROJECT']['SprintMilestonePrefix'] in milestone.title, milestones))

for sprint in sprints:
    process_sprint(sprint, time_tracking)

print("\n")
print("***********Overall Break Down***********")
print_time_tracking(time_tracking)
