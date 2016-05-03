import slackweb
import requests
import envvars
from hashids import Hashids

from django.shortcuts import render
from django.views.generic.base import TemplateView, View
from django.views.generic import ListView
from django.http import HttpResponse, HttpResponseNotAllowed, HttpResponseRedirect
from django.contrib.auth.models import User
from django.contrib.auth import login
from django.core.urlresolvers import reverse, reverse_lazy
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.contrib.auth import logout
from django.core.context_processors import csrf
from django.http import Http404

from models import GoogleUser, SentFeedback, ReceivedFeedback
from hashs import UserHasher as Hasher
hashids = Hashids(min_length=16)

envvars.load()


def get_slack_users():
    """Helper function to return all slack users."""

    slack_token_url = envvars.get('SLACK_TOKEN_URL')
    resp = requests.get(slack_token_url)
    return resp.json()['members']


def get_slack_username(email):
    """Helper function to get user id from username."""

    members = get_slack_users()
    for member in members:
        if member.get('profile').get('email') == email:
            return member.get('name')



class AuthenticationView(TemplateView):

    template_name = 'feedback/authentication.html'

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated():
            return HttpResponseRedirect(
                reverse_lazy('messenger:conversations'))
        return super(AuthenticationView, self).dispatch(request, *args, **kwargs)


class GoogleAuthenticateView(View):

    def get(self, request, *args, **kwargs):

        next_value = request.GET.get('next')
        user_id = request.GET.get('sub')

        try:
            google_user = GoogleUser.objects.get(google_id=user_id)
            user = User.objects.get(id=google_user.app_user.id)
            user.backend = 'django.contrib.auth.backends.ModelBackend'
            login(request, user)

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

        if next_value:
            return HttpResponse("success_next", content_type="text/plain")
        else:
            return HttpResponse("success_home", content_type="text/plain")


class UserHomeView(TemplateView):

    template_name = 'feedback/home.html'


class LoginRequiredMixin(object):

    """View mixin which requires that the user is authenticated."""

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        return super(LoginRequiredMixin, self).dispatch(
            request, *args, **kwargs)


class SignOutView(View, LoginRequiredMixin):

    """Logout User from session."""

    def get(self, request, *args, **kwargs):
        logout(request)
        return HttpResponse("success", content_type="text/plain")


class SendFeedbackView(View, LoginRequiredMixin):

    def post(self, request):
        name = request.POST.get('slack_username', '')
        message = request.POST.get('slack_message', '')
        user_id = request.user.id
        user = User.objects.get(id=user_id)
        reply_hash = Hasher.gen_hash(user)
        reply_hash_url = request.build_absolute_uri(
                reverse(
                    'reply_feedback',
                    kwargs={'reply_hash': reply_hash},
                )
            )

        slack_api_url = envvars.get('SLACK_API_URL')
        slack = slackweb.Slack(url=slack_api_url)
        response = slack.notify(text=message + ' reply to ' + reply_hash_url , channel=name, username="phantom-bot", icon_emoji=":ghost:")
        if response == 'ok':
            sent_feedback = SentFeedback(
                                sender=user,
                                receiver=name,
                                message=message,
                            )
            sent_feedback.save()
        return HttpResponse("success", content_type="text/plain")


class ReplyFeedbackView(TemplateView):

    template_name = 'feedback/reply.html'

    def get(self, request, *args, **kwargs):
        """Handles GET requests to 'reply_message' named route.

        Returns: A redirect to the login page.
        Raises: A Http404 error.
        """
        args = {}

        # get the activation_hash captured in url
        reply_hash = kwargs['reply_hash']

        # reverse the hash to get the user (auto-authentication)
        user = Hasher.reverse_hash(reply_hash)

        if user is not None:
            reply_email = user.email
            sender_id = user
            slack_reply_user = get_slack_username(reply_email)
            sender_feedback = SentFeedback.objects.filter(sender=sender_id)[0]

            user_id = request.user.id
            user = User.objects.get(id=user_id)

            r_feedback = ReceivedFeedback(
                receiver=user,
                slack_username=sender_feedback.receiver,
                message=sender_feedback.message
            )

            r_feedback.save()

            slack_user = slack_reply_user.encode('base64', 'strict')
            args['reply'] = slack_user
            args.update(csrf(request))

            return render(request, self.template_name, args)

        else:
            raise Http404("/User does not exist")


class RespondToFeedbackView(TemplateView):

    def post(self, request, *args, **kwargs):
        name = request.POST.get('slack_username', '')
        name = name.decode('base64', 'strict')
        message = request.POST.get('slack_message', '')

        user_id = request.user.id
        user = User.objects.get(id=user_id)
        reply_hash = Hasher.gen_hash(user)
        reply_hash_url = request.build_absolute_uri(
                            reverse(
                                'reply_feedback',
                                kwargs={'reply_hash': reply_hash},
                            )
                        )

        slack_api_url = envvars.get('SLACK_API_URL')
        slack = slackweb.Slack(url=slack_api_url)
        response = slack.notify(text=message + ' reply to ' + reply_hash_url, channel='@' + name, username="phantom-bot", icon_emoji=":ghost:")
        if response == 'ok':
            sent_feedback = SentFeedback(
                                sender=user,
                                receiver=name,
                                message=message,
                            )
            sent_feedback.save()
        return HttpResponse("success", content_type="text/plain")


class SendFeedbackListView(ListView):
    template_name = 'feedback/sentfeedback.html'
    context_object_name = 'sent_list'

    def get_queryset(self):
        return SentFeedback.objects.filter(sender=self.request.user)

class ReceivedFeedbackListView(ListView):
    template_name = 'feedback/receivedfeedback.html'
    context_object_name = 'received_list'

    def get_queryset(self):
        return ReceivedFeedback.objects.filter(receiver=self.request.user)
