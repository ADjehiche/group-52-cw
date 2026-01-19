from __future__ import annotations

from django.contrib import admin

# Register your models here.
from .models import Item, Bid, Question, Answer

admin.site.register(Item)
admin.site.register(Bid)
admin.site.register(Question)
admin.site.register(Answer)
