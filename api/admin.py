from __future__ import annotations

from django.contrib import admin

from .models import Bid, Item, PageView

admin.site.register(PageView)
admin.site.register(Item)
admin.site.register(Bid)
