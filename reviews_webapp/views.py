from django.shortcuts import redirect, render
from django.views.generic import View, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import CharField, Value
from itertools import chain

from .forms import TicketForm, SubscriptionForm, ReviewForm
from .models import UserFollows, Ticket, Review
from authentication.models import User


class FeedPageView(LoginRequiredMixin, View):
    
    def get(self, request):
        username = request.user
        user_id = request.user.id
        subscriptions = [user.followed_user.id for user in UserFollows.objects.filter(user=1)]
        subscriptions.append(user_id)        

        context = {
            "user": username,
            "posts": get_posts(subscriptions),
        }
        return render(request, 'reviews_webapp/feed.html', context)


class PostsPageView(LoginRequiredMixin, View):
    template_name = "reviews_webapp/my_posts.html"

    def get(self, request):
        username = request.user
        user_id = request.user.id

        context = {
            "user": username,
            "posts": get_posts([user_id]),
        }
        return render(request, self.template_name, context)

    def post(self, request):
        delete_post(request)
        return self.get(request)


class SubscriptionPageView(LoginRequiredMixin, View):
    """View for subscription page. Requires to be logged in."""
    template_name = "reviews_webapp/subscriptions.html"
    sub_form = SubscriptionForm()
    subscriptions = [relationship_object for relationship_object in UserFollows.objects.filter(user=User.objects.get(pk=1))]
    followers = [relationship_object.user for relationship_object in UserFollows.objects.filter(followed_user=User.objects.get(pk=1))]

    def get(self, request):
        context = {
            "form": self.sub_form,
            "subscriptions": self.subscriptions,
            "subscribers": self.followers,
        }
        return render(request, self.template_name, context)

    def post(self, request):
        loggedin_username = request.user
        loggedin_user = User.objects.filter(username=loggedin_username)[0]

        if (request.POST.get("username")):
            added_username = request.POST["username"]

            # TODO verify form is valid 
            # AKA user exists and relationship doesnt't exist
            print(self.sub_form.is_valid())

            if len(User.objects.filter(username=added_username)) == 1 and added_username != loggedin_user:
                new_relationship = UserFollows(user=loggedin_user, followed_user=User.objects.filter(username=added_username)[0])
                new_relationship.save()
            
        elif (request.POST.get("unsubscribe_id")):
            id_to_remove = request.POST["unsubscribe_id"]
            relationship_to_delete = UserFollows.objects.get(pk=id_to_remove)
            relationship_to_delete.delete()

        context = {
            "form": SubscriptionForm(request.POST),
            "subscriptions": [relationship_object for relationship_object in UserFollows.objects.filter(user=User.objects.get(pk=1))],
            "subscribers": self.followers,
        }
        return render(request, self.template_name, context)


class TicketPageView(LoginRequiredMixin, DetailView):
    """A view to create or update tickets."""
    template = 'reviews_webapp/review_details.html'

    def get(self, request, ticket_id):
        if ticket_id == "new":
            context = {
                'title': "Créer un ticket",
                'ticket_form': TicketForm(),
            }
        else:
            ticket = Ticket.objects.get(pk=ticket_id)
            if ticket.user == request.user: 
                context = {
                    "title": "Modifier un ticket",
                    'ticket_form': TicketForm(instance = ticket),
                }
            else:
                context = {
                    'read_only': False if ticket.user == request.user else True, 
                    'ticket': ticket,
                }
        return render(request, self.template, context)

    def post(self, request, ticket_id):
        if ticket_id == "new":
            form = TicketForm(request.POST, request.FILES)
            if form.is_valid():
                ticket = form.save(commit=False)
                ticket.user = request.user
                ticket.save()
        else:
            ticket = Ticket.objects.get(pk=ticket_id)
            form = TicketForm(request.POST, request.FILES, instance = ticket)
            if form.is_valid():
                ticket = form.save(commit=False)
                ticket.save()
        return redirect('posts')


class ReviewPageView(LoginRequiredMixin, DetailView):
    """A view to create or update tickets."""
    template = 'reviews_webapp/review_details.html'

    def get(self, request, ticket_id):
        if ticket_id == 'new':
            context = {
                'title': "Créer une critique",
                'ticket_form': TicketForm(),
                'review_form': ReviewForm(),
            }
            return render(request, self.template, context)
        else: 
            ticket = Ticket.objects.get(pk=ticket_id)
            try:
                review = Review.objects.get(ticket__id=ticket_id)
                context = {
                    'title': "Ecrire une critique",
                    'ticket': ticket,
                    'review_form': ReviewForm(instance = review),
                }
                return render(request, self.template, context)
            except Review.DoesNotExist:
                context = {
                    "title": "Modifier une critique",
                    'ticket': ticket,
                    'review_form': ReviewForm()
                }            
                return render(request, self.template, context)

    def post(self, request, ticket_id):
        if ticket_id == 'new':
            pass
        else:
            review = Review.objects.filter(ticket__id=ticket_id)
            if review.exists():
                form = ReviewForm(request.POST, instance = review[0])
                if form.is_valid():
                    review = form.save(commit=True)
                return self.get(request, ticket_id)
            else:
                form = ReviewForm(request.POST)
                if form.is_valid():
                    review = form.save(commit=False)
                    review.user = request.user
                    review.ticket = Ticket.objects.get(pk=ticket_id)
                    review.save()
                return self.get(request, ticket_id)


def delete_post(request):
    id_to_delete = request.POST["post_id"]
    ticket_to_delete = Ticket.objects.get(pk=id_to_delete)
    ticket_to_delete.image.delete(save=True)
    ticket_to_delete.delete()

def get_posts(users_to_display):
    tickets = Ticket.objects.filter(user__id__in=users_to_display).order_by('-time_created')
    tickets = tickets.annotate(content_type=Value('TICKET', CharField()))

    reviews = Review.objects.filter(user__id__in=users_to_display).order_by('-time_created')
    reviews = reviews.annotate(content_type=Value('REVIEW', CharField()))

    posts = sorted(
        chain(reviews, tickets),
        key=lambda post:post.time_created,
        reverse=True
    )
    return posts