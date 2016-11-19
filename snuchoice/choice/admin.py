from django.contrib import admin
from .models import (
    Election,
    Party,
    Candidate,
    Press,
    Question,
    Answer,
    AnswerHistory,
)

admin.site.register(Election)
admin.site.register(Party)
admin.site.register(Candidate)
admin.site.register(Press)
admin.site.register(Question)
admin.site.register(Answer)
admin.site.register(AnswerHistory)
