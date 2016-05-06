# This module defines utilities for integrating Phantom Messenger with Slack.
import envvars
import slackweb
import requests
import base64
from Crypto.Cipher import AES

from django.conf import settings
from django.core.urlresolvers import reverse

envvars.load()
secret_key = envvars.get('SECRET_KEY')


def get_slack_users():
    """
    Helper function to return all slack users.
    """
    slack_token_url = envvars.get('SLACK_TOKEN_URL')
    response = requests.get(slack_token_url)
    return response.json()['members']


def get_slack_name(user):
    """
    Helper function to get user's slack name.
    """
    members = get_slack_users()
    slack_name = None
    for member in members:
        if member.get('profile').get('email') == user.email:
            slack_name = member.get('name')
            break
    return slack_name


def slack_name_exists(slack_name):
    """
    Helper function to check if slack name exists on the team.
    """
    members = get_slack_users()
    exists = False

    if slack_name.startswith('@'):
        slack_name = slack_name[1:]
    for member in members:
        if member.get('name') == slack_name:
            exists = True
            break
    return exists


def validate_slack_name(slack_name):
    if slack_name.startswith('#'):
        return None
    if not slack_name.startswith('@'):
        slack_name = '@{}'.format(slack_name)
    if not slack_name_exists(slack_name):
        return None
    return slack_name


def get_slack_join_link(request, conversation, slack_name):
    """
    Returns a url a user can follow to join the specified
    conversation from slack.
    """
    join_string = '{}:{}'.format(conversation.pk, slack_name).rjust(32)
    cipher = AES.new(secret_key, AES.MODE_ECB)
    join_hash = base64.b64encode(cipher.encrypt(join_string))
    join_link = request.build_absolute_uri(
        reverse(
            'messenger:conversation_slack_join',
            kwargs={'join_hash': join_hash},
        )
    )
    return join_link


def get_slack_join_conversation(request, join_hash):
    """
    Returns the id of the conversation a user to be joined
    after following the slack join_link.
    Validates that the user is not an impostor attempting
    to join someone else's conversation.
    """
    cipher = AES.new(secret_key, AES.MODE_ECB)
    join_string = cipher.decrypt(base64.b64decode(join_hash)).strip()
    conversation_id, slack_name = tuple(join_string.split(':'))
    user_slack_name = get_slack_name(request.user)
    if slack_name == '@{}'.format(user_slack_name):
        return conversation_id
    else:
        return None


def notify_on_slack(message, slack_name, join_link):
    """
    Formats and sends a message to a user on slack.
    Appends the join_link to the message so the recipient
    can join the message conversation and reply.
    """
    message_text = '{}\n\nReply <{}|here...>'.format(
        message.content,
        join_link,
    )
    fallback_text = '{}: {}| Reply here {}'.format(
        message.conversation.subject,
        message.content,
        join_link,
    )
    attachments = [{
        'title': message.conversation.subject,
        'title_link': join_link,
        'color': '#00B383',
        'text': message_text,
        'thumb_url': settings.APP_ICON_URL,
        'fallback': fallback_text,
        'mrkdwn_in': ['text'],
    }]
    slack = slackweb.Slack(url=envvars.get('SLACK_API_URL'))
    response = slack.notify(
        channel=slack_name,
        username="phantom-bot",
        attachments=attachments,
        icon_emoji=":ghost:",
    )
    message.success = True if response == 'ok' else False
    message.save()
