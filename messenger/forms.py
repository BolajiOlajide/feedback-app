from django import forms
from slack import validate_slack_name


class StartConversationForm(forms.Form):
    """Defines and validates of the start conversation inputs."""

    subject = forms.CharField(max_length=128, widget=forms.TextInput(attrs={'placeholder': 'Feedback on All Hands meeting'}))
    invite = forms.CharField(max_length=128, widget=forms.TextInput(attrs={'placeholder': '@user'}))
    message = forms.CharField(widget=forms.Textarea)

    def clean_invite(self):
        """
        Validate that the invite field is not a channel.
        Also checks that it is a valid slack username.
        """
        data = self.cleaned_data.get('invite')
        data = validate_slack_name(data)

        if data is None:
            raise forms.ValidationError(
                "That is not a valid username on slack!"
            )

        return data


class PostMessageForm(forms.Form):
    """Defines and validates post a message inputs."""

    content = forms.CharField()
