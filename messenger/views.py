import envvars

from django.core.urlresolvers import reverse
from django.views.generic.base import View
from django.db.models import Q
from django.conf import settings
from django.contrib import messages
from django.http import Http404
from django.shortcuts import (
    render,
    redirect,
    get_object_or_404,
)
from django.core.paginator import (
    Paginator,
    EmptyPage,
    PageNotAnInteger,
)

from feedback.views import LoginRequiredMixin
from forms import StartConversationForm, PostMessageForm
from models import Conversation, Message
from slack import (
    get_slack_name,
    get_slack_join_link,
    get_slack_join_conversation,
    notify_on_slack,
)


envvars.load()
secret_key = envvars.get('SECRET_KEY')


class ConversationListView(View, LoginRequiredMixin):
    """
    Shows a list of conversations in which the user is a member.
    """

    def get(self, request, *args, **kwargs):
        """
        Handles GET requests to 'conversations route.
        The following optional GET params can be set to customize the
        returned content:

        :q:         Keyword to filters/search. Returns only conversations
                    where the subject or the content any of it's messages
                    contains the keyword.

        :init:      Set this flag to '1' to only conversations
                    initiated by the current user.

        :items:     Set this flag to '1' to render and return only <li/>
                    without the other page elements. Ideal for loading and
                    appending more items to the list for infinite scroll.

        :page:      The index of the pagination page to render.
        """

        # fetch the querystring param values
        search_keyword = request.GET.get('q')
        initiated_only = request.GET.get('init')
        items_only = request.GET.get('items')
        page = request.GET.get('page')

        # get the user's conversations
        conversations = request.user.initiated_conversations \
            if initiated_only == '1' else request.user.conversations

        # filter conversations by search keyword if specified
        if search_keyword:
            conversations = conversations.filter(
                Q(subject__icontains=search_keyword) |
                Q(messages__content__icontains=search_keyword)
            )

        # paginate results:
        paginator = Paginator(
            conversations.all(),
            settings.CONVERSATION_LIST_PAGE
        )
        try:
            conversations = paginator.page(page)
        except PageNotAnInteger:
            conversations = paginator.page(1)
        except EmptyPage:
            conversations = paginator.page(paginator.num_pages)

        # set the context and template to render:
        context = {
            'conversations': conversations,
            'search_keyword': search_keyword,
        }
        template = 'messenger/conversation_items.html' \
            if items_only == '1' else 'messenger/conversations.html'
        return render(request, template, context)


class ConversationStartView(View, LoginRequiredMixin):
    """
    Shows and processes the form to start a new conversation and
    send the initial message to the invited member(s).
    """

    def get(self, request, *args, **kwargs):
        """
        Handles GET requests to 'conversations/start/' route.
        """
        form = StartConversationForm()
        context = {'form': form}
        template = 'messenger/conversation_start.html'
        return render(request, template, context)

    def post(self, request, *args, **kwargs):
        """
        Handles POST requests to 'conversations/start/' route.
        """
        form = StartConversationForm(request.POST)
        if form.is_valid():
            # first create and save a new conversation instance:
            conversation = Conversation(
                subject=form.cleaned_data.get("subject"),
                initiator=request.user
            )
            conversation.save()
            # add the current user as a member of the coversation:
            conversation.members.add(request.user)
            # create and save the new message instance:
            message = Message(
                content=form.cleaned_data.get("message"),
                user=request.user,
                conversation=conversation
            )
            message.save()
            # send the slack message notification:
            slack_name = form.cleaned_data.get("invite")
            join_link = get_slack_join_link(
                request,
                conversation,
                slack_name
            )
            notify_on_slack(message, slack_name, join_link)
            # redirect to the conversation view:
            return redirect(reverse(
                'messenger:conversation', kwargs={'pk': conversation.pk}
            ))
        else:
            messages.add_message(
                request,
                messages.ERROR,
                "Please fill in the fields correctly."
            )

        context = {'form': form}
        template = 'messenger/conversation_start.html'
        return render(request, template, context)


class ConversationView(View, LoginRequiredMixin):
    """
    Shows a conversation thread with its the messages.
    Also handles posting of new messages to the coversation.
    """

    def get(self, request, *args, **kwargs):
        """
        Handles GET requests to 'conversations/<id>/' route.
        """
        pk = kwargs.get('pk')
        conversation = get_object_or_404(Conversation, id=pk)
        if request.user not in conversation.members.all():
            raise Http404("Amebo! Mind your business.")

        form = PostMessageForm()

        context = {
            'conversation': conversation,
            'form': form,
        }
        template = 'messenger/conversation.html'
        return render(request, template, context)

    def post(self, request, *args, **kwargs):
        """
        Handles POST requests to 'conversations/<id>/' route.
        The POST data should be the message to be posted on the
        conversation thread. The message notification is sent to
        the other member(s) of the conversation.
        """
        pk = kwargs.get('pk')
        conversation = get_object_or_404(Conversation, id=pk)
        form = PostMessageForm(request.POST)
        if form.is_valid():
            # get the other members of the conversation:
            other_members = conversation.members.exclude(id=request.user.id)
            if other_members.count():
                # create and save the new message instance:
                message = Message(
                    content=form.cleaned_data.get("content"),
                    user=request.user,
                    conversation=conversation
                )
                message.save()
                # send the message notification to the other member(s)
                # of the conversation:
                slack_names = ['@{}'.format(get_slack_name(member))
                               for member in other_members]
                for slack_name in slack_names:
                    join_link = get_slack_join_link(
                        request,
                        conversation,
                        slack_name
                    )
                    notify_on_slack(message, slack_name, join_link)
            else:
                messages.add_message(
                    request,
                    messages.INFO,
                    """Sorry, you cannot continue this conversation
                     until the invited user joins in."""
                )
        else:
            messages.add_message(
                request,
                messages.ERROR,
                "Something's wrong with the your message format!"
            )

        context = {
            'conversation': conversation,
            'form': form,
        }
        template = 'messenger/conversation.html'
        return render(request, template, context)


class ConversationSlackJoinView(View, LoginRequiredMixin):
    """
    Handles the process of joining a user to a conversation using
    the join link from slack. Performs validation checks to deter
    impostors.
    """

    def get(self, request, *args, **kwargs):
        """
        Handles GET requests to 'conversations/<join_hash>/slack_join' route.
        """
        join_hash = kwargs.get('join_hash')
        conversation_id = get_slack_join_conversation(request, join_hash)
        conversation = get_object_or_404(Conversation, id=conversation_id)
        conversation.members.add(request.user)

        # redirect to the conersation view:
        return redirect(reverse(
            'messenger:conversation', kwargs={'pk': conversation.pk},
        ))
