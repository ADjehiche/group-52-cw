"""Django admin configuration for CBay models."""

from django.contrib import admin

from .models import Bid, Follow, Item, Question, User, Answer

admin.site.register(User)
admin.site.register(Item)
admin.site.register(Bid)
admin.site.register(Question)
admin.site.register(Answer)
admin.site.register(Follow)
