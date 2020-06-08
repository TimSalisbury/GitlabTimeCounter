# GitlabTimeCounter
While working on a group project for University we found that Gitlab had no easy way to view
the total time spent per person per sprint (where Sprints were designated Milestones). This is
a simple Python script that will calculate the total time spent per person on a per sprint basis,
and also an overall time spent per person across all sprints (milestones). 

## How To Use
### Have all requirements installed
Requirements can be found in requirements.txt, simply use `pip install -r requirements.txt`

### Define a config.ini
In order to run the script you need to give it certain information. To do this, simply create a
file called `config.ini` in the same directory as the python script. config.ini is required to
have two sections, `AUTHENTICATION` and `PROJECT`. The `AUTHENTICATION` section simply defines
required values for authentication with your given GitLab server. These are:
* `GitLabServer` e.g. `https://gitlab.com/` 
* `PersonalAccessToken` e.g. `ABCDEFGHI12345` See https://docs.gitlab.com/ee/user/profile/personal_access_tokens.html

`PROJECT` defines project specific attributes, these are:
* `ID` e.g. `123` This is the ID of your project
* `SprintMilestonePrefix` e.g. `Sprint` This is prefix to all Sprint milestones, for example, if your 
sprint Milestones were named: `Sprint 1`, `Sprint 2`, `Sprint 3` then your prefix would be `Sprint`
* OPTIONAL: `Lab-time-log` e.g. `Lab-time-log`, this is used if you wish to include your meeting time in the breakdown.
Note that your meeting tables have to follow a quite specific format for this to work properly. 

Here is an example `config.ini`:
```ini
[AUTHENTICATION]
GitLabServer = https://gitlab.com/
PersonalAccessToken = ABCDEFGHI12345

[PROJECT]
ID = 123
SprintMilestonePrefix = Sprint
LabTimeWikiSlug = Lab-time-log
```