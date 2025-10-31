from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse

from .models import UserProfile, Reaction


class ReactionViewTests(TestCase):
    def setUp(self):
        # Users
        self.owner = User.objects.create_user(username='owner', password='pass12345')
        self.other = User.objects.create_user(username='other', password='pass12345')

        # Profiles (assign minimal required fields; set profile_picture name to avoid file writes)
        self.owner_profile = UserProfile.objects.create(
            user=self.owner,
            firstname='Owner', lastname='User', age=30,
            gender='M', address='123 Owner St',
            profile_picture='profile_pictures/owner.jpg',
        )

        self.other_profile = UserProfile.objects.create(
            user=self.other,
            firstname='Other', lastname='User', age=25,
            gender='F', address='456 Other Ave',
            profile_picture='profile_pictures/other.jpg',
        )

        self.client = Client()

    def login_other(self):
        self.client.login(username='other', password='pass12345')

    def login_owner(self):
        self.client.login(username='owner', password='pass12345')

    def test_like_toggle_non_ajax(self):
        self.login_other()
        url = reverse('react_profile', args=[self.owner_profile.pk])

        # Like once -> increment
        res = self.client.post(url, {'reaction': Reaction.LIKE})
        self.assertEqual(res.status_code, 302)
        prof = UserProfile.objects.get(pk=self.owner_profile.pk)
        self.assertEqual(prof.likes_count, 1)
        self.assertEqual(prof.loves_count, 0)
        self.assertEqual(prof.dislikes_count, 0)

        # Like again -> toggle off -> decrement
        res = self.client.post(url, {'reaction': Reaction.LIKE})
        self.assertEqual(res.status_code, 302)
        prof = UserProfile.objects.get(pk=self.owner_profile.pk)
        self.assertEqual(prof.likes_count, 0)
        self.assertEqual(prof.loves_count, 0)
        self.assertEqual(prof.dislikes_count, 0)

    def test_switch_reaction_ajax(self):
        self.login_other()
        url = reverse('react_profile', args=[self.owner_profile.pk])

        # Like via AJAX
        res = self.client.post(
            url, {'reaction': Reaction.LIKE},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest', HTTP_ACCEPT='application/json'
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data['my_reaction'], Reaction.LIKE)
        self.assertEqual(data['likes_count'], 1)
        self.assertEqual(data['loves_count'], 0)
        self.assertEqual(data['dislikes_count'], 0)

        # Switch to love -> like--, love++
        res = self.client.post(
            url, {'reaction': Reaction.LOVE},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest', HTTP_ACCEPT='application/json'
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data['my_reaction'], Reaction.LOVE)
        self.assertEqual(data['likes_count'], 0)
        self.assertEqual(data['loves_count'], 1)
        self.assertEqual(data['dislikes_count'], 0)

    def test_self_reaction_blocked_ajax(self):
        self.login_owner()
        url = reverse('react_profile', args=[self.owner_profile.pk])
        res = self.client.post(
            url, {'reaction': Reaction.LIKE},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest', HTTP_ACCEPT='application/json'
        )
        self.assertEqual(res.status_code, 400)
        data = res.json()
        self.assertIn('error', data)
        prof = UserProfile.objects.get(pk=self.owner_profile.pk)
        self.assertEqual(prof.likes_count, 0)
        self.assertEqual(prof.loves_count, 0)
        self.assertEqual(prof.dislikes_count, 0)
from django.test import TestCase

# Create your tests here.
