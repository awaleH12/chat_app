from django.db import models

# Create your models here.
class UserProfile(models.Model):
    id = models.AutoField(primary_key=True)
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

    def __str__(self):
        return f"{self.firstname} {self.lastname}"