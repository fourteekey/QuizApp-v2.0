from django.core.management.base import BaseCommand
from quiz.models import TypeQuestion


class Command(BaseCommand):
    help = 'Наполнить базу данных, базовыми типами вопросов.'

    def handle(self, *args, **kwargs):
        types_question = ({'id': 1, 'name': 'Ответ текстом'},
                          {'id': 2, 'name': 'Выбрать ответ'},
                          {'id': 3, 'name': 'Выбрать несколько вариантов'},)
        for _ in types_question: TypeQuestion.objects.create(id=_['id'], name=_['name'])
