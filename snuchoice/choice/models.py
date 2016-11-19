import datetime
import random
from django.conf import settings
from django.contrib.staticfiles.templatetags.staticfiles import static
from django.db import models
from django.dispatch import receiver
from django.urls import reverse
from django.utils import timezone


def upload_directory_path(modelname, fieldname):
    global path

    def path(instance, filename):
        return "{}/{}/{}_{}.{}".format(
            modelname,
            instance.pk,
            fieldname,
            timezone.now().strftime("%M%S"),
            filename.split(".")[-1],
        )
    return path


class Election(models.Model):

    name = models.CharField(max_length=30, unique=True)

    # 총학: 0, 단대: 단과대학 순번 (>0)
    college_order = models.PositiveSmallIntegerField(default=0)

    def __str__(self):
        return self.name

    @classmethod
    def get_college_elections(cls):
        college_elections = cls.objects.exclude(college_order=0).order_by(
            "college_order")
        return college_elections.exclude(party__isnull=True)


class Party(models.Model):

    election = models.ForeignKey(Election, models.SET_NULL,
        blank=True, null=True, related_name="parties")

    name = models.CharField(max_length=30)
    slogan = models.CharField(max_length=100, blank=True)
    color = models.CharField(max_length=6, blank=True)

    logo = models.FileField(upload_to=upload_directory_path("party", "logo"),
        blank=True, null=True)  # svg 가능하도록
    book = models.FileField(upload_to=upload_directory_path("party", "book"),
        blank=True, null=True)
    leaflet = models.FileField(upload_to=upload_directory_path("party", "leaflet"),
        blank=True, null=True)

    class Meta:
        verbose_name_plural = "parties"

    def __str__(self):
        return "{}({})".format(self.name, self.election.name)

    def get_absolute_url(self):
        return reverse("party_detail", args=[self.pk])


class Candidate(models.Model):

    election = models.ForeignKey(Election, models.SET_NULL,
        blank=True, null=True, related_name="candidates")
    party = models.ForeignKey(Party, models.SET_NULL,
        blank=True, null=True, related_name="candidates")

    name = models.CharField(max_length=30)
    _position = models.BooleanField(verbose_name="정후보 여부")
    photo = models.ImageField(upload_to=upload_directory_path("candidate", "photo"),
        blank=True, null=True)

    class Meta:
        ordering = ('party', '-_position')

    def __str__(self):
        return "{} {}({}) {}".format(
            self.name, self.party.name, self.election.name, self.position)

    @property
    def position(self):
        return "정" * self._position or "부"

    def get_photo_url(self):
        try:
            return self.photo.url
        except ValueError:
            return static("img/face.png")


@receiver(models.signals.pre_save, sender=Candidate)
def set_election_field(sender, instance, **kwargs):
    if instance.party.election:
        instance.election = instance.party.election


class Press(models.Model):

    name = models.CharField(max_length=30)
    logo = models.FileField(upload_to=upload_directory_path("press", "logo"),
        blank=True, null=True)
    homepage = models.URLField(blank=True, null=True)
    facebook = models.URLField(blank=True, null=True)

    class Meta:
        verbose_name_plural = "presses"

    def __str__(self):
        return self.name


class Question(models.Model):

    THRESHOLD = 100
    TIMEDELTA = datetime.timedelta(hours=48)
    ADDITIONAL_TIMEDELTA = datetime.timedelta(hours=24)

    election = models.ForeignKey(Election, models.SET_NULL,
        blank=True, null=True, related_name="questions")
    author = models.ForeignKey(settings.AUTH_USER_MODEL, models.SET_NULL,
        blank=True, null=True, related_name="created_questions")
    author_name = models.CharField(max_length=30, blank=True)  # 탈퇴 시 백업용
    author_email = models.EmailField(blank=True)  # 탈퇴 시 백업용

    voters = models.ManyToManyField(settings.AUTH_USER_MODEL, through='Vote',
        related_name="voted_questions")

    title = models.CharField(max_length=100)
    answer_content_limit = models.PositiveSmallIntegerField(default=800)

    initial_order = models.PositiveSmallIntegerField(default=0)
    questionnaire_sent = models.DateTimeField(blank=True, null=True)
    delayed_candidates = models.ManyToManyField(Candidate, blank=True,
        related_name="+")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return "{}. {}".format(self.pk, self.title)

    def get_absolute_url(self):
        return reverse("question_detail", args=[self.pk])

    def get_achievement_percent(self):
        count = self.voters.count()
        percent = count / self.THRESHOLD * 100
        return min(percent, 100)

    def get_votes_left(self):
        return max(Question.THRESHOLD - self.voters.count(), 0)

    def get_answer_list(self, stance=None):
        answer_list = self.answer_set.order_by('?')
        if stance is not None:
            return answer_list.filter(stance=stance)
        else:
            return answer_list

    def get_for_answer_list(self):
        return self.get_answer_list(stance=True)

    def get_aga_answer_list(self):
        return self.get_answer_list(stance=False)

    def get_replied_candidate_list(self):
        return [answer.candidate for answer in self.answer_set.all()]

    def get_unreplied_candidate_list(self):
        unreplied_candidate_list = []
        for candidate in self.election.candidate_set.all():
            if not Answer.objects.filter(question=self, candidate=candidate).exists():
                unreplied_candidate_list += [candidate]
        random.shuffle(unreplied_candidate_list)
        return unreplied_candidate_list

    def get_html_meta_author(self):
        if self.written_by_press():
            return self.author.press.name
        else:
            et_al = (" 외 {}명".format(self.voters.count() - 1)
                if self.voters.count() > 1 else "")
            return self.author.get_full_name() + et_al

    def past_deadline(self, hard=False):
        if self.questionnaire_sent:
            deadline = self.questionnaire_sent + self.TIMEDELTA
            deadline += self.ADDITIONAL_TIMEDELTA * hard
            return timezone.now() > deadline
        else:
            return False

    def past_hard_deadline(self):
        return self.past_deadline(hard=True)

    def written_by_press(self):
        return self.author.is_journalist


class Vote(models.Model):

    question = models.ForeignKey(Question, models.CASCADE, related_name="votes")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, models.CASCADE,
        related_name="votes")
    time = models.DateTimeField(auto_now_add=True)


class Answer(models.Model):

    question = models.ForeignKey(Question, models.PROTECT,
        related_name="answers")
    candidate = models.ForeignKey(Candidate, models.SET_NULL,
        blank=True, null=True, related_name="answers")

    stance = models.NullBooleanField()  # 질문에 대한 찬반. 답변 거부 시 null
    content = models.TextField(max_length=4095)

    def __str__(self):
        return "질문 {}에 대한 {}의 답변".format(
            self.question.pk, self.candidate.name if self.candidate else None)

    def get_trimmed_content(self):
        # 워드에서 엔터를 카운트하지 않아서, 여기에서도 엔터를 카운트하지 않도록 함.
        content_limit = self.question.answer_content_limit + 1
        current_string = ""
        current_length = 0
        for line in self.content.splitlines():
            if current_length < content_limit:
                current_string += line[:(content_limit - current_length)]
                current_string += "\n"
                current_length += len(line)
        return current_string.rstrip()

    def past_content_limit(self):
        content_limit = self.question.answer_content_limit + 1
        content_without_newlines = "".join(self.content.splitlines())
        return len(content_without_newlines) > content_limit


class AnswerHistory(models.Model):

    answer = models.ForeignKey(Answer, models.CASCADE, related_name="histories")
    stance = models.NullBooleanField()
    content = models.TextField()
    time = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "answer histories"
