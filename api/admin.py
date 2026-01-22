from __future__ import annotations

from django.contrib import admin

# Register your models here.
from .models import AnswerLike, Bid, Follow, Item, Question, QuestionLike, User, Answer

admin.site.register(User)
admin.site.register(Item)
admin.site.register(Bid)
admin.site.register(Question)
admin.site.register(Answer)
admin.site.register(Follow)
admin.site.register(QuestionLike)
admin.site.register(AnswerLike)

