from __future__ import print_function
from gitmirror import gitmirror
from flask import request, jsonify
import requests
import sys
import json
import os
import git
import subprocess


################
# STATUS CODES #
################
ERMAGERD = 500
NOTFOUND = 404
INVALID = 403
NOTPROCESSED = 202
CREATED = 201
OK = 200

##########################################
# Environments specific, constant values #
##########################################
#TEAM = ["devops", "netops", "sysops", "extra"]
#TARGET_API_URL = "https://34.214.65.7/api/v4/" # dependent on environment
TEAM = None
TARGET_REMOTE_URL = None
TARGET_API_URL = None
IDENTITY = None
TOKEN = None

def init():
    global TEAM
    global TARGET_API_URL
    global TARGET_REMOTE_URL
    global IDENTITY
    global TOKEN
    print ("init the things du") # debug print
    with open('/home/git-mirror/etc/mirror.conf','r') as initfile:
        content = initfile.read().splitlines()
    init = {}
    for line in content:
        if line[0] != '#':
            init[line.split(' = ')[0]] = line.split(' = ')[1]
    init['team'] = init['team'].split(',')
    print (init) # debug print

    TEAM = init['team']
    TARGET_REMOTE_URL = init['target_remote_url']
    TARGET_API_URL = init['target_api_url']
    IDENTITY = init['identity']
    TOKEN = init['target_api_token']
##################################
# Functions for dealing with git #
##################################
# clone repo from source
def clone_repo(repo_data):
    print ("clone") # debug print
    org = check_org(repo_data['repository']['full_name'])
    repo = check_repo(repo_data['repository']['full_name'])
    dir_path = '/home/git-mirror/repos/' + \
                org
    repo_path = '/home/git-mirror/repos/' + \
                org + '/' + repo
    try:
        if not os.path.isdir(repo_path):
            if not os.path.isdir(dir_path):
                os.makedirs(dir_path)
            pull_source = subprocess.Popen(\
                            ['git','clone','--mirror',\
                            repo_data['repository']['url']],\
                             cwd=dir_path, stderr=subprocess.PIPE)
            pull_source.wait()
            print ("clone")
        else:
            pull_source = subprocess.Popen(\
                            ['git','fetch'],
                            cwd=repo_path, stderr=subprocess.PIPE)
            pull_source.wait()
            print ("fetch")
    except OSError as e:
        return {'error':'Error cloning repo'}
    return True

# mirror source repo to target repo
def mirror_repo(repo_data):
    # testing
    print ("mirror") # debug print 
    print (repo_data['repository']['git_url']) # debug print
    return_data = {"mirror":repo_data['repository']['git_url']}
    # /testing
    # git push -mirror origin
    # mirror da damn ting du
    org = check_org(repo_data['repository']['full_name'])
    repo = check_repo(repo_data['repository']['full_name'])
    dir_path = '/home/git-mirror/repos/' + \
                org
    repo_path = '/home/git-mirror/repos/' + \
                org + '/' + repo
    remotes = []
    remote_exists = False

    if not os.path.isdir(dir_path):
        return {'error': 'ayyyyyyy something shit the bed hard my friend'}

    output = subprocess.Popen(\
                        ['git','remote','-v'],\
                        cwd=repo_path,\
                        stderr=subprocess.PIPE,\
                        stdout=subprocess.PIPE)
    lines = output.communicate()[0].splitlines()
    for line in lines:
        remotes.append(line)
    print (remotes) # debug print
    for remote in remotes:
        if remote.find(TARGET_REMOTE_URL) != -1 and remote.find('push') != -1:
            remote_exists = True
            break
    if not remote_exists:
        ouptut = subprocess.Popen(\
                        ['git','remote','set-url','--push','origin',\
                        TARGET_REMOTE_URL + '-git_mirror' + ':' + org + '/' + repo],\
                        cwd=repo_path,\
                        stderr=subprocess.PIPE,\
                        stdout=subprocess.PIPE)
        #print (output.communicate[0])
    mirror_target = subprocess.Popen(\
                                    ['git','push','--mirror',\
                                    TARGET_REMOTE_URL + '-git_mirror' + ':' + org + '/' + repo],\
                                    cwd=repo_path,\
                                    stderr=subprocess.PIPE,\
                                    stdout=subprocess.PIPE)
    #print (mirror_target.communicate[0])
    return True

# init target repo
def create_repo(repo_data,target_access_token):
    # testing
    print ("create") # debug print
    print (repo_data['repository']['full_name']) # debug print
    return_data = {"create":repo_data['repository']['full_name']}
    # create repo in target
    #headers = {'PRIVATE-TOKEN': target_access_token, 'Content-Type': 'application/json'}
    headers = {'PRIVATE-TOKEN': target_access_token}
    try:
        print ('create 1')
        print (repo_data)
        organization = check_org(repo_data['repository']['full_name'])
        if not organization:
            print (organization)
            return ({"error":"Cannot determine organization"})
        api_request = TARGET_API_URL + 'namespaces?search=' + organization
        print ('create_repo api req')
        print (organization)
        with requests.Session() as s:
            r = s.get(api_request,headers=headers)
            print (r)
    except:
        print ('create 2')
        return ({"error":"Cannot make api request"})
    namespace = r.json()[0]
    if not namespace:
        print ('create 3')
        return ({"error":"Cannot find organization in namespaces"})
    try:
        print ('create 4')
        headers = {'PRIVATE-TOKEN': target_access_token}
        api_request = TARGET_API_URL + 'projects'
        payload = {'name': repo_data['repository']['name'],\
                    'namespace_id': namespace['id']}
        with requests.Session() as s:
            print ('create 5')
            r = s.post(api_request,headers=headers,data=payload)
    except:
        print ("Cannot make api request (create)") # debug print
        return ({"error":"Cannot make API request (create)"})
    # add remote

    return r.status_code

# determine what team the source repo belongs to
def check_org (org_repo):
    print ("Check ORG")
    print (org_repo)
    for i in range(0,len(TEAM)):
        if org_repo.split("/")[0].lower() == TEAM[i]:
            return TEAM[i]
    return False

def check_repo (org_repo):
    print ("Check REPO")
    print (org_repo)
    return org_repo.split("/")[1].lower() + '.git'

# does target repo exist already?
def verify_target_repo(repo_data):
    print ('verify') # debug print
    # get gitlab_url.domain/organization/repo
    return_data = []
    with requests.Session() as s:
        try:
            #target_access_token = os.environ["PERSONAL_ACCESS_TOKEN"]
            target_access_token = 'wom8muiBZLNtVa4QqR2m'
        except KeyError:
            print ("Error: KeyError on access token") # debug print
            sys.exit(1)

        headers = {'PRIVATE-TOKEN': target_access_token, 'Content-Type': 'application/json'}
        try:
            print ("test") # debug print
            api_request = TARGET_API_URL + 'projects/'
            with requests.Session() as s:
                print (api_request) # debug print
                r = s.get(api_request,headers=headers)
        except:
            print ("Cannot make api request (verify)") # debug print
            return ({"error":"Cannot make api request (verify)"})
        repos = r.json()
        found_repo = {}
        for repo in repos:
            if repo['path_with_namespace'] == repo_data['repository']['full_name']:
                found_repo = repo['path_with_namespace']
                print (found_repo) # debug print
                break
        if not found_repo:
            print ("didn't find repo du")
            create_status = create_repo(repo_data,target_access_token)
            try:
                if not 'error' in create_status:
                    if not create_status == CREATED:
                        # deal with http status codes
                        print ("status codes bruh") # debug print
                        print (create_status) # debug print
                        return {"error":"Eh bad status code returned on target repo creation bro"}
            except TypeError as e:
                pass
        clone = clone_repo(repo_data)
        print ("CLONE")
        print (clone)
        try:
            if 'error' in clone:
                print ("Error: " + clone) # debug print
                return clone
        except TypeError as e:
            pass
        mirror = mirror_repo(repo_data)
        print ("MIRROR")
        print (mirror)
        try:
            if 'error' in mirror:
                print ("Error: " + mirror) # debug print
                return mirror
        except TypeError as e:
            pass
        return True

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
    return_obj = []
    init()
    # debug 
    print (TEAM) # debug print
    print (TARGET_API_URL) # debug print
    # /debug
    # ensure git url exists, else return error code
    git_url_source = repo_data['repository']['git_url']
    org_repo_source = repo_data['repository']['full_name']
    organization = check_org(org_repo_source)
    if organization is not False:
        print ('org: ' + organization) # debug print
        return_obj.append(verify_target_repo(repo_data))
        #print ('return_obj: ' + return_obj)
        print (return_obj)
        for object in return_obj:
            try:
                if 'error' in object:
                    print ("there's a snake in my boots") # debug print
                    return jsonify(return_obj)
            except TypeError as e:
                pass
    else:
        status = NOTFOUND
        print ('awww yisss')
        return_obj.append({"error":"organization is false"})
    #
    print (return_obj)
    return jsonify(return_obj)
