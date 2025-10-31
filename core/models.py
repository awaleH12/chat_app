from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError

# Create your models here.
class UserProfile(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='profile',
        null=True, blank=True,
    )
    firstname = models.CharField(max_length=30)
    lastname = models.CharField(max_length=30)
    age = models.PositiveIntegerField()
    # Restrict gender to a choice between Male and Female
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
    ]
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, blank=True, null=True)
    address = models.TextField()
    profile_picture = models.ImageField(upload_to='profile_pictures/')
    # Denormalized reaction counters
    likes_count = models.PositiveIntegerField(default=0)
    loves_count = models.PositiveIntegerField(default=0)
    dislikes_count = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"{self.firstname} {self.lastname}"


class Reaction(models.Model):
    LIKE = 'like'
    LOVE = 'love'
    DISLIKE = 'dislike'
    REACTION_CHOICES = [
        (LIKE, 'Like'),
        (LOVE, 'Love'),
        (DISLIKE, 'Dislike'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='reactions')
    profile = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='reactions')
    reaction = models.CharField(max_length=7, choices=REACTION_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'profile')
        indexes = [
            models.Index(fields=['profile', 'reaction']),
            models.Index(fields=['user']),
        ]

    def __str__(self):
        return f"{self.user} {self.reaction} {self.profile}"

    def clean(self):
        # Prevent reacting to your own profile at the model level
        if self.profile_id and self.user_id and self.profile.user_id == self.user_id:
            raise ValidationError("You can't react to your own profile.")

    def save(self, *args, **kwargs):
        # Ensure clean() is called even when saving programmatically
        self.full_clean()
        return super().save(*args, **kwargs)