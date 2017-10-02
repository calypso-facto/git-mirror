from gitmirror import gitmirror
from flask import request, jsonify

@gitmirror.route('/')
@gitmirror.route('/index')
def index():
    return "Howdy ya'll"

@gitmirror.route('/devops', methods=[ 'POST' ])
def devops():
    return "DevOps"

@gitmirror.route('/netops', methods=[ 'POST' ])
def netops():
    return "NetOps"

@gitmirror.route('/sysops', methods=[ 'POST' ])
def sysops():
    return "SysOps"
