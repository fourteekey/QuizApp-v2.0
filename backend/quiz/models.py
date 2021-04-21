from django.db import models
from django.conf import settings


class Quiz(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100)
    description = models.CharField(max_length=1000)
    created = models.DateTimeField(auto_now_add=True)
    start = models.DateTimeField()
    end = models.DateTimeField()
    archived = models.BooleanField(null=True, default=False)
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'quiz'


class TypeQuestion(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'type_question'


class Question(models.Model):
    id = models.AutoField(primary_key=True)
    quiz = models.ForeignKey('Quiz', on_delete=models.CASCADE)
    question = models.CharField(max_length=4000)
    position = models.IntegerField()
    archived = models.BooleanField(null=True, default=False)
    type_question = models.ForeignKey('TypeQuestion', on_delete=models.DO_NOTHING)


    def __str__(self):
        return self.question

    class Meta:
        db_table = 'questions'
        ordering = ('position',)


class VariableAnswer(models.Model):
    id = models.AutoField(primary_key=True)
    text = models.CharField(max_length=200)
    question = models.ForeignKey('Question', on_delete=models.CASCADE)

    def __str__(self):
        return self.text

    class Meta:
        db_table = 'variable_answer'


class UserAnswer(models.Model):
    id = models.AutoField(primary_key=True)
    visitor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    answer_text = models.CharField(max_length=1000, blank=True, null=True, default=None)
    created = models.DateTimeField(auto_now_add=True)
    question = models.ForeignKey('Question', on_delete=models.CASCADE)
    variable_answer = models.ManyToManyField('VariableAnswer')

    class Meta:
        db_table = 'visitor_answers'
