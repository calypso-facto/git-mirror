from gitmirror import gitmirror
from flask import request, jsonify
from __future__ import print_function
import requests
import sys
import json
import os
'''
Need to:
    1. Identify hq repo owning team
    2. Identify if repo exists in gitlab
        a. yes, git fetch -p origin; git push --mirror origin
        b. no, git clone --mirror; <foofara>; git remote-url origin <gitlab>; etc.etc.etc.
    3. Team ownership needs to be retained

    org_repo = payload['repository']['full_name'] = organization/repo-name (need verification)
    if org_repo.split("/")[0].lower() == TEAM[x]:
        do things
*******************
* new repo mirror *
*******************
git clone --mirror <github.url>/<organization>/<repo name>
git remote set-url --push origin git@<gitlab.url>:<organization>/<repo name>
git push --mirror
'''


################
# STATUS CODES #
################
ERMAGERD = 500
NOTFOUND = 404
INVALID = 403
NOTPROCESSED = 202
OK = 200

##########################################
# Environments specific, constant values #
##########################################
TEAM = ["devops", "netops", "sysops"]
TARGET_API_URL = "https://34.214.65.7/api/v4/" # dependent on

##################################
# Functions for dealing with git #
##################################
# mirror source repo to target repo
def mirror_repo(repo_data):
    print ("mirror") # debug print
    # git push -mirror origin

# init target repo
def create_repo(repo_data):
    print ("create") # debug print
    # init bare repo
    # git remote add origin <target url>

# determine what team the source repo belongs to
def check_org (org_repo):
    for i in range(0,len(TEAM)):
        #    # from for j in... return TEAM[i] 
        #    # is a less eficient way of accomplishing
        #    # the same goal iff the json posted from 
        #    # a github webhook does not change
        #    # ie. the <organization>/<repo name>
        #    # convention is followed in github repo
        #    # creation. This is a policy dependent thing
        #    # so it might change in the future and break this.
        #    for j in range(0,len(org_repo.split("/"))):
        #        if org_repo.split("/")[j].lower() == TEAM[i]:
        #            return TEAM[i]
        if org_repo.split("/")[0].lower() == TEAM[i]:
            return TEAM[i]
    return False

# does target repo exist already?
def verify_target_repo(repo_data):
    print ('verify') # debug print
    # get gitlab_url.domain/organization/repo
    with requests.Session() as s:
        try:
            target_access_token = os.environmen["PERSONAL_ACCESS_TOKEN"]
        except KeyError:
            print ("Need to return error")
            sys.exit(1)

        headers = {'PRIVATE-TOKEN': target_access_token}
        try:
            api_request = TARGET_API_URL + \
                          'projects/' + \
                          repo_data['repository']['full_name'].split("/")[0] + \
                          '2%F' + \
                          repo_data['repository']['full_name'].split("/")[1]
            r = s.get(TARGET_API_URL+repo_data['repository']['full_name'],headers=headers)
        except:
            print ("Cannot make api request")
            sys.exit(1)

        if r.status_code == requests.codes.ok:
            # repo exists in target
            mirror_repo(repo_data)
        else:
            # repo does not exist... yet
            create_repo(repo_data)
            mirror_repo(repo_data)
        return r.status_code
##########
# ROUTES #
##########
# testing/generic
#################
# These routes don't actually do anything.
# They are for verifying the application is running
@gitmirror.route('/')
@gitmirror.route('/index')
def index():
    return "Howdy ya'll"

# Mirror Git Repo Route
#######################
# This route does all the work
# It accepts an application/json object from
# a GitHub Webhook and ensures the necessary
# fields exist, calls the check_org and
# verify_target_repo functions, then returns
# a status code 
@gitmirror.route('/mirror', methods=[ 'POST' ])
def webhook():
    repo_data = request.get_json(silent=True)
    status = OK

    # ensure git url exists, else return error code
    try: 
        git_url_source = repo_data['repository']['git_url']
        org_repo_source = repo_data['repository']['full_name']
    except:
        status = NOTFOUND

    organization = check_org(org_repo_source)
    if organization is not False:
        print (organization) # debug print
        verify_target_repo(repo_data)
    else:
        status = NOTFOUND
    return "wienerschnitzel"
