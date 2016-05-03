from django import forms


class StartConversationForm(forms.Form):
    """
    defines and validates of the start conversation inputs.
    """
    subject = forms.CharField(max_length=128)
    invite = forms.CharField(max_length=128)
    message = forms.CharField(widget=forms.Textarea)


class PostMessageForm(forms.Form):
    """
    defines and validates post a message inputs.
    """
    content = forms.CharField()
