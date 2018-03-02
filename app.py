#!/usr/bin/env python3

import json
import argparse

from flask import Flask
from flask import request
from flask import jsonify
from bot import Bot

app = Flask(__name__)

class GitlabBot(Bot):
    def __init__(self):
        try:
            self.authmsg = open('authmsg').read().strip()
        except:
            raise Exception("The authorization messsage file is invalid")

        super(GitlabBot, self).__init__()
        self.chats = {}
        try:
            chats = open('chats', 'r').read()
            self.chats = json.loads(chats)
        except:
            open('chats', 'w').write(json.dumps(self.chats))

        self.send_to_all('Hi !')

    def text_recv(self, txt, chatid):
        ''' registering chats '''
        txt = txt.strip()
        if txt.startswith('/'):
            txt = txt[1:]
        if txt == self.authmsg:
            if str(chatid) in self.chats:
                self.reply(chatid, "\U0001F60E  boy, you already got the power.")
            else:
                self.reply(chatid, "\U0001F60E  Ok boy, you got the power !")
                self.chats[chatid] = True
                open('chats', 'w').write(json.dumps(self.chats))
        elif txt == 'shutupbot':
            del self.chats[chatid]
            self.reply(chatid, "\U0001F63F Ok, take it easy\nbye.")
            open('chats', 'w').write(json.dumps(self.chats))
        else:
            self.reply(chatid, "\U0001F612 I won't talk to you.")

    def send_to_all(self, msg):
        for c in self.chats:
            self.reply(c, msg)


b = GitlabBot()


@app.route("/", methods=['GET', 'POST'])
def webhook():
    data = request.json
    # json contains an attribute that differenciates between the types, see
    # https://docs.gitlab.com/ce/user/project/integrations/webhooks.html
    # for more infos
    kind = data['object_kind']
    if kind == 'push':
        msg = generatePushMsg(data)
    elif kind == 'tag_push':
        msg = generatePushMsg(data)  # TODO:Make own function for this
    elif kind == 'issue':
        msg = generateIssueMsg(data)
    elif kind == 'note':
        msg = generateCommentMsg(data)
    elif kind == 'merge_request':
        msg = generateMergeRequestMsg(data)
    elif kind == 'wiki_page':
        msg = generateWikiMsg(data)
    elif kind == 'pipeline':
        msg = generatePipelineMsg(data)
    elif kind == 'build':
        msg = generateBuildMsg(data)
    b.send_to_all(msg)
    return jsonify({'status': 'ok'})


def generatePushMsg(data):
    msg = '*{0} ({1}) - {2} new commits*\n'\
        .format(data['project']['name'], data['project']['default_branch'], data['total_commits_count'])
    for commit in data['commits']:
        msg = msg + '----------------------------------------------------------------\n'
        msg = msg + commit['message'].rstrip()
        msg = msg + '\n' + commit['url'].replace("_", "\_") + '\n'
    msg = msg + '----------------------------------------------------------------\n'
    return msg


def generateIssueMsg(data):
    action = data['object_attributes']['action']
    if action == 'open':
        msg = '*{0} new Issue for {1}*\n'\
            .format(data['project']['name'], data['assignee']['name'])
    elif action == 'close':
        msg = '*{0} Issue closed by {1}*\n'\
            .format(data['project']['name'], data['user']['name'])
    msg = msg + '*{0}*\n'.format(data['object_attributes']['title'])
    msg = msg + 'see [URL]({0}) for further details'.format(data['object_attributes']['url'])
    return msg


def generateCommentMsg(data):
    ntype = data['object_attributes']['noteable_type']
    return generateNoteMsgByType(ntype, data)

def generateNoteMsgByType(ntype, data):
    ntypeMsg = 'Note'
    if ntype == 'Commit':
        ntypeMsg = 'Note to Commit'
    elif ntype == 'MergeRequest':
        ntypeMsg = 'Note to MergeRequest'
    elif ntype == 'Issue':
        ntypeMsg = 'Note to Issue'
    elif ntype == 'Snippet':
        ntypeMsg = 'Note on Code snippet'
    msg = '*{0} new {2} from {1} to {3}*\n' \
        .format(data['project']['name'], data['user']['name'], ntypeMsg, data['object_attributes']['assignee']['name'])
    msg = msg + '*{0}*\n'.format(data['object_attributes']['note'])
    msg = msg + 'see [URL]({0}) for further details'.format(data['object_attributes']['url'])
    return msg


def generateMergeRequestMsg(data):
    action = data['object_attributes']['state']
    last_commit = data['object_attributes']['last_commit']
    if action == 'opened':
        msg = '*{0} new Merge Request from {1}*\n' \
            .format(data['project']['name'], last_commit['author']['name'])
    elif action == 'updated':
        msg = '*{0} Merge Request updated by {1}*\n' \
            .format(data['project']['name'], last_commit['author']['name'])
    elif action == 'merged':
        msg = '*{0} Merge Request merged by {1}*\n' \
            .format(data['project']['name'], last_commit['author']['name'])
    elif action == 'closed':
        msg = '*{0} Merge Request closed by {1}*\n' \
            .format(data['project']['name'], last_commit['author']['name'])
    msg = msg + '*{0}*\n'.format(data['object_attributes']['title'])
    msg = msg + 'see [{0}]({1}) for further details'.format(data['object_attributes']['title'], data['object_attributes']['url'])
    return msg


def generateWikiMsg(data):
    return 'new wiki stuff'


def generatePipelineMsg(data):
    return 'new pipeline stuff'


def generateBuildMsg(data):
    return 'new build stuff'


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, help='listening port', default=11011)
    parser.add_argument('--interface', metavar='i', type=str, help='listening iface', default='0.0.0.0')
    args = parser.parse_args()

    b.run_threaded()
    app.run(host=args.interface, port=args.port)
