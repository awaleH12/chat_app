from django.shortcuts import render, get_object_or_404
from . import models
from . import forms
from django.shortcuts import redirect
from .forms import UserProfileForm
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import authenticate, login
from django.db import transaction
from django.db.models import F
from django.http import JsonResponse

# Create your views here.
@login_required
def profile_view(request):
    # Show all profiles
    profiles = models.UserProfile.objects.all()
    my_profile = models.UserProfile.objects.filter(user=request.user).first()
    return render(request, 'core/profile.html', {
        'profiles': profiles,
        'my_profile': my_profile,
    })

@login_required
def create_profile(request):
    # If the user already has a profile, send them to view/edit it
    existing = models.UserProfile.objects.filter(user=request.user).first()
    if existing:
        messages.info(request, 'You already have a profile.')
        return redirect('view_profile', pk=existing.pk)

    if request.method == "POST":
        form = UserProfileForm(request.POST, request.FILES)
        if form.is_valid():
            profile = form.save(commit=False)
            profile.user = request.user
            profile.save()
            messages.success(request, 'Profile created successfully.')
            return redirect('view_profile', pk=profile.pk)
    else:
        form = UserProfileForm()
    return render(request, "core/create_profile.html", {'form': form})


@login_required
def delete_profile(request, pk):
    """Confirm and delete a UserProfile by primary key.

    GET: render confirmation page.
    POST: delete and redirect to profile list.
    """
    profile = get_object_or_404(models.UserProfile, pk=pk)
    if profile.user != request.user:
        messages.error(request, "You don't have permission to delete this profile.")
        return redirect('view_profile', pk=profile.pk)
    if request.method == 'POST':
        profile.delete()
        messages.success(request, 'Profile deleted.')
        return redirect('profile_view')
    return render(request, 'core/delete_profile.html', {'profile': profile})


@login_required
def view_profile(request, pk):
    """Show a single profile with options to edit or delete."""
    profile = get_object_or_404(models.UserProfile, pk=pk)
    # Find the current user's reaction if any
    my_reaction = None
    try:
        from .models import Reaction
        my_reaction = Reaction.objects.filter(user=request.user, profile=profile).first()
    except Exception:
        my_reaction = None
    return render(request, 'core/profile_detail.html', {'profile': profile, 'my_reaction': my_reaction})


@login_required
def edit_profile(request, pk):
    """Edit an existing profile."""
    profile = get_object_or_404(models.UserProfile, pk=pk)
    if profile.user != request.user:
        messages.error(request, "You don't have permission to edit this profile.")
        return redirect('view_profile', pk=profile.pk)
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated.')
            return redirect('view_profile', pk=profile.pk)
    else:
        form = UserProfileForm(instance=profile)
    return render(request, 'core/edit_profile.html', {'form': form, 'profile': profile})


@login_required
def my_profile(request):
    """Redirect the current user to their own profile detail, or to create one."""
    profile = models.UserProfile.objects.filter(user=request.user).first()
    if profile:
        return redirect('view_profile', pk=profile.pk)
    messages.info(request, "You don't have a profile yet. Let's create one.")
    return redirect('create_profile')


@login_required
def profile_settings(request):
    """Go to edit page for the user's profile or to create if none exists."""
    profile = models.UserProfile.objects.filter(user=request.user).first()
    if profile:
        return redirect('edit_profile', pk=profile.pk)
    messages.info(request, "Create your profile to access settings.")
    return redirect('create_profile')


@login_required
def react_profile(request, pk):
    """Create, update, or remove a reaction for the given profile.

    Behavior:
    - If no existing reaction: create it and increment the matching counter.
    - If existing reaction matches the selected: remove it (toggle off) and decrement the counter.
    - If existing reaction differs: update it and adjust counters accordingly.
    """
    # Detect AJAX/JSON request
    is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest' or (
        'application/json' in (request.headers.get('accept') or '')
    )

    if request.method != 'POST':
        if is_ajax:
            return JsonResponse({'error': 'Method not allowed'}, status=405)
        return redirect('view_profile', pk=pk)

    profile = get_object_or_404(models.UserProfile, pk=pk)
    # Disallow reacting to your own profile
    if profile.user_id == request.user.id:
        if is_ajax:
            return JsonResponse({'error': "You can't react to your own profile."}, status=400)
        messages.error(request, "You can't react to your own profile.")
        return redirect('view_profile', pk=pk)
    reaction_value = request.POST.get('reaction')
    from .models import Reaction
    allowed = {Reaction.LIKE, Reaction.LOVE, Reaction.DISLIKE}
    if reaction_value not in allowed:
        if is_ajax:
            return JsonResponse({'error': 'Invalid reaction.'}, status=400)
        messages.error(request, 'Invalid reaction.')
        return redirect('view_profile', pk=pk)

    from django.core.exceptions import ValidationError
    try:
        with transaction.atomic():
            existing = Reaction.objects.select_for_update().filter(user=request.user, profile=profile).first()
            if existing is None:
                # create new reaction
                Reaction.objects.create(user=request.user, profile=profile, reaction=reaction_value)
                if reaction_value == Reaction.LIKE:
                    models.UserProfile.objects.filter(pk=profile.pk).update(likes_count=F('likes_count') + 1)
                elif reaction_value == Reaction.LOVE:
                    models.UserProfile.objects.filter(pk=profile.pk).update(loves_count=F('loves_count') + 1)
                else:
                    models.UserProfile.objects.filter(pk=profile.pk).update(dislikes_count=F('dislikes_count') + 1)
            else:
                if existing.reaction == reaction_value:
                    # toggle off: delete existing and decrement
                    if existing.reaction == Reaction.LIKE:
                        models.UserProfile.objects.filter(pk=profile.pk).update(likes_count=F('likes_count') - 1)
                    elif existing.reaction == Reaction.LOVE:
                        models.UserProfile.objects.filter(pk=profile.pk).update(loves_count=F('loves_count') - 1)
                    else:
                        models.UserProfile.objects.filter(pk=profile.pk).update(dislikes_count=F('dislikes_count') - 1)
                    existing.delete()
                else:
                    # change reaction: decrement old, increment new
                    if existing.reaction == Reaction.LIKE:
                        models.UserProfile.objects.filter(pk=profile.pk).update(likes_count=F('likes_count') - 1)
                    elif existing.reaction == Reaction.LOVE:
                        models.UserProfile.objects.filter(pk=profile.pk).update(loves_count=F('loves_count') - 1)
                    else:
                        models.UserProfile.objects.filter(pk=profile.pk).update(dislikes_count=F('dislikes_count') - 1)

                    existing.reaction = reaction_value
                    existing.save(update_fields=['reaction', 'updated_at'])

                    if reaction_value == Reaction.LIKE:
                        models.UserProfile.objects.filter(pk=profile.pk).update(likes_count=F('likes_count') + 1)
                    elif reaction_value == Reaction.LOVE:
                        models.UserProfile.objects.filter(pk=profile.pk).update(loves_count=F('loves_count') + 1)
                    else:
                        models.UserProfile.objects.filter(pk=profile.pk).update(dislikes_count=F('dislikes_count') + 1)
    except ValidationError as e:
        if is_ajax:
            return JsonResponse({'error': "; ".join(e.messages)}, status=400)
        messages.error(request, "; ".join(e.messages))

    # Prepare fresh values and current reaction
    from .models import Reaction
    profile = models.UserProfile.objects.get(pk=profile.pk)
    current = Reaction.objects.filter(user=request.user, profile=profile).first()

    if is_ajax:
        return JsonResponse({
            'status': 'ok',
            'likes_count': profile.likes_count,
            'loves_count': profile.loves_count,
            'dislikes_count': profile.dislikes_count,
            'my_reaction': current.reaction if current else None,
        })

    return redirect('view_profile', pk=pk)


def signup(request):
    """Register a new user using Django's built-in UserCreationForm.

    On success, automatically log the user in and redirect to the profile list.
    """
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Authenticate with the credentials just set to attach a backend
            raw_password = form.cleaned_data.get('password1')
            authenticated = authenticate(request, username=user.username, password=raw_password)
            if authenticated is not None:
                login(request, authenticated)
                messages.success(request, 'Welcome! Your account has been created.')
                # After signup, if no profile exists, direct to create profile
                if not models.UserProfile.objects.filter(user=authenticated).exists():
                    messages.info(request, 'Let\'s complete your profile.')
                    return redirect('create_profile')
                return redirect('profile_view')
            messages.info(request, 'Account created. Please log in.')
            return redirect('login')
    else:
        form = UserCreationForm()
    return render(request, 'registration/signup.html', {'form': form})