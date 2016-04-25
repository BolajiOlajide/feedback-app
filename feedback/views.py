import slackweb
import requests
import envvars

from django.views.generic.base import TemplateView, View
from django.http import HttpResponse, HttpResponseNotAllowed
from django.contrib.auth.models import User
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.contrib.auth import logout

from models import GoogleUser

envvars.load()

def get_slack_users():
    '''Helper function to return all slack users.'''

    slack_token_url = envvars.get('SLACK_TOKEN_URL')
    resp = requests.get(slack_token_url)
    return resp.json()['members']


def get_slack_user_id(username):
    '''Helper function to get user id from username '''

    members = get_slack_users()
    for member in members:
        if member.get('name') == username:
            return member.get('id')


class AuthenticationView(TemplateView):

    template_name = 'feedback/authentication.html'


class GoogleAuthenticateView(View):

    def get(self, request, *args, **kwargs):

        user_id = request.GET['sub']
        try:
            google_user = GoogleUser.objects.get(google_id=user_id)
            user = User.objects.get(id=google_user.app_user.id)
            user.backend = 'django.contrib.auth.backends.ModelBackend'
            login(request, user)

            return HttpResponse("success", content_type="text/plain")

        except GoogleUser.DoesNotExist:

            if 'hd' not in request.GET:
                return HttpResponseNotAllowed("Invalid parameters given")

            if (
                request.GET['hd'] != 'andela.com' and
                request.GET['iss'] != "accounts.google.com" and
                request.GET['email_verified'] != "true" and
                request.GET['aud'] != "21865176717-u4dio2k0teg84v27mlrpruvigveeua7i.apps.googleusercontent"
            ):

                return HttpResponseNotAllowed("Invalid parameters given")

            # proceed to create the user
            username = request.GET['name']

            # Create the user
            # need to find alternate data for these fields
            user = User(
                username=username,
                email=request.GET["email"],
                first_name=request.GET['given_name'],
                last_name=request.GET['family_name']
            )
            user.save()

            google_user = GoogleUser(google_id=user_id,
                                     app_user=user,)

            user.backend = 'django.contrib.auth.backends.ModelBackend'

            google_user.save()

            login(request, user)
            return HttpResponse("success", content_type="text/plain")


class UserHomeView(TemplateView):

    template_name = 'feedback/home.html'


class LoginRequiredMixin(object):

    '''View mixin which requires that the user is authenticated.'''

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        return super(LoginRequiredMixin, self).dispatch(
            request, *args, **kwargs)


class SignOutView(View, LoginRequiredMixin):

    '''Logout User from session.'''

    def get(self, request, *args, **kwargs):
        logout(request)
        return HttpResponse("success", content_type="text/plain")


class SendFeedbackView(View, LoginRequiredMixin):

    def post(self, request):
        name = request.POST.get('slack_username', '')
        message = request.POST.get('slack_message', '')
        slack_api_url = envvars.get('SLACK_API_URL')
        slack = slackweb.Slack(url=slack_api_url)
        slack.notify(text=message, channel=name, username="phantom-bot", icon_emoji=":ghost:")
        return HttpResponse("success", content_type="text/plain")
