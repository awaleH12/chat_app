from django.contrib import admin
from .models import UserProfile



@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
	list_display = ('firstname', 'lastname', 'age', 'get_gender_display')
	list_filter = ('gender',)
	readonly_fields = ()

	def get_gender_display(self, obj):
		return obj.get_gender_display()
	get_gender_display.short_description = 'Gender'

