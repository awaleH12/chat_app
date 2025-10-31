from django.shortcuts import render, get_object_or_404
from . import models
from . import forms
from django.shortcuts import redirect
from .forms import UserProfileForm
from django.contrib import messages

# Create your views here.
def profile_view(request):
    # Show all profiles
    profiles = models.UserProfile.objects.all()
    return render(request, 'core/profile.html', {'profiles': profiles})

def create_profile(request):
    if request.method == "POST":
        form = UserProfileForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('profile_view')  # Adjust to your profile list view name
    else:
        form = UserProfileForm()
    return render(request, "core/create_profile.html", {'form': form})


def delete_profile(request, pk):
    """Confirm and delete a UserProfile by primary key.

    GET: render confirmation page.
    POST: delete and redirect to profile list.
    """
    profile = get_object_or_404(models.UserProfile, pk=pk)
    if request.method == 'POST':
        profile.delete()
        messages.success(request, 'Profile deleted.')
        return redirect('profile_view')
    return render(request, 'core/delete_profile.html', {'profile': profile})


def view_profile(request, pk):
    """Show a single profile with options to edit or delete."""
    profile = get_object_or_404(models.UserProfile, pk=pk)
    return render(request, 'core/profile_detail.html', {'profile': profile})


def edit_profile(request, pk):
    """Edit an existing profile."""
    profile = get_object_or_404(models.UserProfile, pk=pk)
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated.')
            return redirect('view_profile', pk=profile.pk)
    else:
        form = UserProfileForm(instance=profile)
    return render(request, 'core/edit_profile.html', {'form': form, 'profile': profile})