from django.contrib import admin

from users.models import PostCheck


# Register your models here.
class PostCheckAdmin(admin.ModelAdmin):
    list_display = ("title", "created_at", "status")  # Customize the list view


# Register the admin class for the model
admin.site.register(PostCheck, PostCheckAdmin)
