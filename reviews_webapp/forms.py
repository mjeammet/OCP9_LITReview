from django import forms
from django.core.exceptions import ValidationError
from django.db.models.base import Model
from django.forms import ModelForm

from authentication.models import User
from reviews_webapp.models import Ticket, Review

class SubscriptionForm(forms.Form):
    username = forms.CharField(max_length=30, initial='Nom d\'utilisateur', required=False)
    # username = forms.IntegerField()

    def is_existing_user(self):
        queryset = User.objects.filter(username = self.username)
        if len(queryset) != 1:
            raise ValidationError("Utilisateur introuvable")
        else:
            return True

class TicketForm(ModelForm):
    class Meta:
        model = Ticket
        fields = ['title', 'description', 'image']
        # exclude = ["user", "time_created"]

class ReviewForm(ModelForm):
    class Meta:
        model = Review
        fields = ['headline', 'rating', 'body']
        body = forms.CharField(widget=forms.Textarea) 
        # exclude = ["user", "time_created"]

class DeleteForm(forms.Form):
    delete_form = forms.BooleanField(widget=forms.HiddenInput, initial=True)