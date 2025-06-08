from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, update_session_auth_hash, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm
from django import forms
from django.http import HttpResponse
from .forms import UserRegistrationForm, UserProfileForm, ProfileForm, LoginForm
from .models import User


def register(request):
    if request.method == 'POST':
        form = ExtendedUserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            username = form.cleaned_data.get('username')
            messages.success(request, f'Account created for {username}! You can now login.')
            return redirect('templates:landing.html')
    else:
        form = ExtendedUserRegistrationForm()
    return render(request, 'registration/register.html', {'form': form})

@login_required
def change_password(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, 'Password changed successfully!')
            return redirect('profile')
    else:
        form = PasswordChangeForm(request.user)

    return render(request, 'users/change_password.html', {'form': form})


@login_required
def user_list(request):
    if not request.user.is_admin:
        messages.error(request, 'You do not have permission to view this page.')
        return redirect('helpdesk:dashboard')

    users = User.objects.all().order_by('username')
    return render(request, 'users/user_list.html', {'users': users})


@login_required
def profile(request):
    user = request.user

    # Create profile if it doesn't exist
    if not hasattr(user, 'profile'):
        from .models import Profile
        Profile.objects.create(user=user)

    user_form = UserProfileForm(request.POST or None, instance=user)
    profile_form = ProfileForm(request.POST or None, request.FILES or None, instance=user.profile)

    if user_form.is_valid() and profile_form.is_valid():
        user_form.save()
        profile_form.save()
        messages.success(request, 'Profile updated successfully!')
        return redirect('profile')

    return render(request, 'users/profile.html', {
        'user_form': user_form,
        'profile_form': profile_form,
    })

def profile_view(request):
    return render(request, 'users/profile.html')

@login_required
def user_detail(request, pk):
    user = get_object_or_404(User, pk=pk)
    return render(request, 'users/user_detail.html', {'user': user})


class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']


def user_update(request, pk):
    user = get_object_or_404(User, pk=pk)

    if request.method == 'POST':
        form = UserUpdateForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, 'User updated successfully.')
            return redirect('user_detail', pk=user.pk)
    else:
        form = UserUpdateForm(instance=user)

    return render(request, 'users/user_update.html', {'form': form, 'user': user})


@login_required
def dashboard_view(request):
    context = {
        'user': request.user,
        'title': 'Dashboard',
    }
    return render(request, 'dashboard.html', context)


def dashboard_simple(request):
    return HttpResponse(f"""
    <h1>HelpDesk Dashboard</h1>
    <p>Welcome {request.user.username if request.user.is_authenticated else 'Guest'}!</p>
    <ul>
        <li><a href="/admin/">Admin Panel</a></li>
        <li><a href="/users/">Users</a></li>
        <li><a href="/knowledgebase/">Knowledge Base</a></li>
        <li><a href="/logout/">Logout</a></li>
    </ul>
    """)


def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('helpdesk:dashboard')
        else:
            return render(request, 'users/login.html', {'error': 'Invalid credentials'})
    return render(request, 'users/login.html')


@login_required
def dashboard_redirect(request):
    return redirect('helpdesk:dashboard')


def user_login(request):
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('dashboard')
    else:
        form = LoginForm()
    return render(request, 'registration/login.html', {'form': form})


class ExtendedUserRegistrationForm(UserRegistrationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
        return user

def logout_view(request):
    logout(request)
    return redirect('templates:landing.html')