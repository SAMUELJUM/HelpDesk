from django.contrib import admin
from tickets.models import Ticket
from tickets.models import Category, Department,TicketCategory
from tickets.models import   TicketComment, TicketStatusChange


admin.site.register(Ticket)
admin.site.register(Category)
admin.site.register(Department)
admin.site.register(TicketCategory)
admin.site.register(TicketComment)
admin.site.register(TicketStatusChange)
