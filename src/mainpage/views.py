from django.contrib import messages
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from .forms import RegisterForm, LoginForm, UpdateUserForm, UpdateProfileForm
from django.contrib.auth.views import LoginView
from django.contrib.auth.decorators import login_required

from .models import Profile, FriendRequest


def mainpage(request):
    return render(request, "mainpage/mainpage.html")


def friends(request):
    user = Profile.objects.get(id=request.user.id)
    all_users = Profile.objects.exclude(id=request.user.id)
    fr = FriendRequest.objects.filter(to_user=user)
    user_friends = user.friends.all()
    for u in all_users:
        if u in user_friends:
            all_users = all_users.exclude(id=u.id)
        if FriendRequest.objects.filter(from_user=user, to_user=u):
            all_users = all_users.exclude(id=u.id)
    return render(request, "mainpage/friends.html", {'all_users': all_users, 'fr': fr, 'user_friends': user_friends})



def favorites(request):
    return render(request, "mainpage/favorites.html")


def meetings(request):
    return render(request, "mainpage/meetings.html")


@login_required
def profile(request):
    if request.method == 'POST':
        user_form = UpdateUserForm(request.POST, instance=request.user)
        profile_form = UpdateProfileForm(request.POST, request.FILES, instance=request.user.profile)

        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, 'Ваш профиль успешно обновлен')
            return redirect(to='profile')
    else:
        user_form = UpdateUserForm(instance=request.user)
        profile_form = UpdateProfileForm(instance=request.user.profile)

    return render(request, 'mainpage/profile.html', {'user_form': user_form, 'profile_form': profile_form})


def send_request(request,id):
    from_user = Profile.objects.get(id=request.user.id)
    to_user = Profile.objects.get(id=id)
    frequest = FriendRequest.objects.get_or_create(from_user=from_user, to_user=to_user)
    return redirect('/friends/')


def accept_request(request, id):
    frequest = FriendRequest.objects.get(id=id)
    user1 = frequest.to_user
    user2 = frequest.from_user
    user1.friends.add(user2)
    user2.friends.add(user1)
    FriendRequest.objects.filter(id=id).delete()
    return redirect('/friends/')


def reject_request(request, id):
    FriendRequest.objects.filter(id=id).delete()
    return redirect('/friends/')


def delete_friend(request, id):
    user = Profile.objects.get(id=request.user.id)
    friend = Profile.objects.get(id=id)
    user.friends.remove(friend)
    friend.friends.remove(user)
    print('\n\n\n\n')
    print(user.friends.all())
    print(friend.friends.all())
    print('\n\n\n\n')
    return redirect('/friends/')


class SignUp(View):
    form_class = RegisterForm
    initial = {'key': 'value'}
    template_name = 'registration/signup.html'

    def dispatch(self, request, *args, **kwargs):
        # will redirect to the home page if a user tries to access the register page while logged in
        if request.user.is_authenticated:
            return redirect(to='/')

        # else process dispatch as it otherwise normally would
        return super(SignUp, self).dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        form = self.form_class(initial=self.initial)
        return render(request, self.template_name, {'form': form})

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)

        if form.is_valid():
            form.save()

            username = form.cleaned_data.get('username')
            messages.success(request, f'Account created for {username}')

            return redirect(to='search')

        return render(request, self.template_name, {'form': form})

class CustomLoginView(LoginView):
    form_class = LoginForm

    def form_valid(self, form):
        remember_me = form.cleaned_data.get('remember_me')

        if not remember_me:
            self.request.session.set_expiry(0)

            # Set session as modified to force data updates/cookie to be saved.
            self.request.session.modified = True

        # else browser session will be as long as the session cookie time "SESSION_COOKIE_AGE" defined in settings.py
        return super(CustomLoginView, self).form_valid(form)