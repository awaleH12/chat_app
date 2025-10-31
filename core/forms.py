from django import forms
from .models import UserProfile


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['firstname', 'lastname', 'age', 'gender', 'address', 'profile_picture']
        widgets = {
            'gender': forms.Select(),
        }

    def clean_profile_picture(self):
        pic = self.cleaned_data.get('profile_picture')
        # Add basic validation if needed (size/type)
        return pic
