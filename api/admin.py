from __future__ import annotations

from django.contrib import admin

# Register your models here.
from .models import Item, Bid, User, Question, Answer, ItemQuestion, ItemAnswer

admin.site.register(Item)
admin.site.register(Bid)
admin.site.register(User)
admin.site.register(Question)
admin.site.register(Answer)
admin.site.register(ItemQuestion)
admin.site.register(ItemAnswer)
