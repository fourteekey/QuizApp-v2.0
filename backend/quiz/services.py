from datetime import datetime
from django.contrib.auth import get_user_model
from .models import *
from .serializers import *


def check_user(user_id):
    user = get_user_model().objects.filter(id=user_id)
    if user: return user[0]


def create_quiz(name, description, date_start, date_end, author):
    try:
        date_start = datetime.strptime(date_start, '%d.%m.%Y %H:%M')
        date_end = datetime.strptime(date_end, '%d.%m.%Y %H:%M')
    except Exception:
        return None
    if date_end < date_start: return None

    quiz = Quiz.objects.create(name=name, description=description, start=date_start, end=date_end, author=author)
    return QuizSerializer(quiz).data


def update_quiz(quiz_id, name, description, date_end, author):
    quiz = Quiz.objects.filter(id=quiz_id, author=author)
    if not quiz: return
    quiz = quiz[0]

    if name: quiz.name = name
    if description: quiz.description = description
    if date_end:
        try:
            date_end = datetime.strptime(date_end, '%d.%m.%Y %H:%M')
        except Exception:
            return None
        if date_end < quiz.start: return None
        quiz.end = date_end

    quiz.save()
    return QuizSerializer(quiz).data


def get_quiz(quiz_id):
    quiz = Quiz.objects.filter(id=quiz_id)

    if not quiz: return None
    return QuizSerializer(quiz[0]).data


def delete_quiz(quiz_id, author):
    quiz = Quiz.objects.filter(id=quiz_id, author=author)

    if not quiz: return None
    quiz = quiz[0]
    quiz.archived = True
    quiz.save()
    return 1


def create_questions(quiz_id, questions, author):
    quiz = Quiz.objects.filter(id=quiz_id, author=author)
    if not quiz: return None
    quiz = quiz[0]

    last_position_question = Question.objects.filter(quiz=quiz).last()
    if last_position_question: last_position_question = last_position_question.position + 1

    i = last_position_question or 0
    for question in questions:
        text = question.get('text', None)
        type_question_id = question.get('type_question', None)
        variable_answers = question.get('variable_answer', [])

        type_question = TypeQuestion.objects.filter(id=type_question_id)

        if type_question and (type_question_id == 1 or (type_question_id in (2, 3,) and variable_answers)):
            question = Question.objects.create(quiz=quiz, question=text, position=i, type_question=type_question[0])
            if type_question_id in (2, 3,):
                for text_answer in variable_answers: VariableAnswer.objects.create(text=text_answer, question=question)
            i += 1

    return QuizSerializer(quiz).data


def update_question(question_id, question, author):
    text = question.get('text', None)
    type_question_id = question.get('type_question', None)
    variable_answers = question.get('variable_answer', [])

    type_question = TypeQuestion.objects.filter(id=type_question_id)
    question = Question.objects.filter(id=question_id, quiz__author=author)
    if not question: return
    question = question[0]

    if text: question.question = text
    if type_question and (type_question_id == 1 or (type_question_id in (2, 3) and variable_answers)):
        # Удалить старые варианты ответа
        if question.type_question.id in (2, 3) and type_question[0].id == 1:
            VariableAnswer.objects.filter(question=question).delete()
        question.type_question = type_question[0]

    if variable_answers and question.type_question.id in (2, 3):
        for text_answer in variable_answers: VariableAnswer.objects.create(text=text_answer, question=question)

    question.save()
    return QuizSerializer(question.quiz).data


def delete_question(question_id, author):
    question = Question.objects.filter(id=question_id, quiz__author=author)
    if not question: return
    question = question[0]

    question.archived = True
    question.save()
    return QuizSerializer(question.quiz).data


def get_active_quiz(user):
    quizzes = Quiz.objects.filter(start__lte=datetime.now(), end__gte=datetime.now(), archived=False).exclude(id__in=UserAnswer.objects.filter(visitor=user).values_list('question__quiz__id', flat=True).distinct())

    return QuizSerializer(quizzes, many=True).data


def validate_answer(visitor_answers, quiz_question_ids, quiz_question):
    i = 0
    for answer in visitor_answers:
        answer_question_id = answer.get('id', 0)
        if answer_question_id not in quiz_question_ids: return '404'
        # Т.к всегда очищаем список и у нас получается нулевой элемент.
        question = quiz_question[quiz_question_ids.index(answer_question_id)+i]
        if question.type_question.id == 1 and not answer.get('text', None):
            return f'Ответ на вопрос {answer_question_id}.\nОтсутсвует текст овтета.'
        elif question.type_question.id in (2, 3) \
                and (not answer.get('variable', None) or list(set(answer['variable']) - set(VariableAnswer.objects.filter(question=question).values_list('id', flat=True)))):
            # Проверяем, чтоб в ответах пользователя не было лишних id.
            return f'Ответ на вопрос {answer_question_id}.\nВ списке отсутсвуют варианты ответов или есть неверные id.'
        quiz_question_ids.remove(answer_question_id)
        i += 1

    return quiz_question_ids


def create_answer_quiz(quiz_id, answers, visitor):
    quiz = Quiz.objects.filter(id=quiz_id
                               ).exclude(id__in=UserAnswer.objects.filter(visitor=visitor).values_list('question__quiz__id', flat=True).distinct())
    if not quiz: return {'error': 'Вы уже проходили этот опрос или опрос недоступен.'}, 1
    quiz_question = Question.objects.filter(quiz=quiz[0], archived=False)
    visitor_answers = answers.get('answers')
    if len(quiz_question) != len(visitor_answers): return {'error': 'Не на все вопросы был предоставлен ответ.'}, 1

    quiz_question_ids = list(quiz_question.values_list('id', flat=True))
    error_answers = validate_answer(visitor_answers, quiz_question_ids, quiz_question)
    if error_answers: return {'error': error_answers}, 1

    # Список очищался при валидации.
    quiz_question_ids = list(quiz_question.values_list('id', flat=True))
    for answer in answers['answers']:
        question = quiz_question[quiz_question_ids.index(answer.get('id'))]
        # Если пользователь шлет лишние ключи
        if question.type_question.id == 1: text = answer.get('text', None)
        else: text = None
        user_answer_obj = UserAnswer(visitor=visitor, answer_text=text, question=question)

        user_answer_obj.save()
        if question.type_question.id == 2:
            user_answer_obj.variable_answer.add(VariableAnswer.objects.get(id=answer['variable'][0]))
        elif question.type_question.id == 3:
            for answer_variable_id in answer['variable']:
                user_answer_obj.variable_answer.add(VariableAnswer.objects.get(id=answer_variable_id))

    return {'detail': 'Ваши ответы записаны.'}, 0


def get_history_answers(visitor):
    quizzes = Quiz.objects.filter(id__in=UserAnswer.objects.filter(visitor=visitor).values_list('question__quiz__id', flat=True).distinct())
    quizzes_serializer = QuizSerializer(quizzes, many=True).data

    for quiz in quizzes_serializer:
        del quiz['questions']
        serializer = HistoryAnswersSerializer(UserAnswer.objects.filter(question__quiz__id=quiz['id']), many=True).data
        quiz.update({'answers': serializer})

    return quizzes_serializer
