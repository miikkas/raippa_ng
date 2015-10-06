import re
import math

import django
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseNotFound
from django.template import Context, RequestContext, loader
from django.core.urlresolvers import reverse
from django.core.servers.basehttp import FileWrapper
from django.utils import timezone
from django.utils.safestring import mark_safe

from courses.models import *

# TODO: A view that displays statistics of a page that has embedded pages.
#       E.g. the average completion status, how many of total course
#       participants have done how much etc.
#       - links to the stats of individual exercises
#           * sorting by completion rate
#           * sorting by total tries, average tries before correct etc.

###########################################################
# Some helper functions which won't be needed after the course enrollment of 
# users and the course instances have been implemented.

def user_evaluation(user, exercise):
    return exercise[1].get_type_object().get_user_evaluation(user)

def user_has_answered(user, exercise):
    return user_evaluation(user, exercise) != "unanswered"

def course_exercises(course):
    exercises = []
    cg = color_generator(parent_pages.count())
    
    for p in parent_pages:
        color = next(cg)
        if p.content.embedded_pages.count() > 0:
            all_pages = list(p.content.embedded_pages.all().order_by('emb_embedded'))
            exercises.extend(list(zip(itertools.cycle([color]), all_pages)))
    return exercises

def filter_users_on_course(users, course):
    exercises = course_exercises(course)
    return [user for user in users 
            if any(user_has_answered(user, exercise) for exercise in exercises)]

def courses_linked(exercise):
    linked = []
    courses = Courses.objects.all()
    
    for course in courses:
        try:
            course.contents.get(content=exercise)
        except ContentGraph.DoesNotExist:
            pass
        else:
            linked.append(course)
    return linked

########################################################### 

def textfield_eval(given, answers):
    given = given.replace("\r\n", "\n").replace("\n\r", "\n")
    correct = True
    hinted = False
    errors = []
    for answer in answers:
        if answer.regexp:
            try:
                if re.match(answer.answer, given) and answer.correct and correct == True:
                    correct = True
                    break
                elif re.match(answer.answer, given) and not answer.correct:
                    correct = False
                    if answer.hint: hinted = True
                elif not re.match(answer.answer, given) and answer.correct:
                    correct = False
            except re.error as e_msg:
                errors.append("Regexp error: " + e_msg)
                correct = False
        else:
            if given == answer.answer and answer.correct and correct == True:
                correct = True
                break
            elif given == answer.answer and not answer.correct:
                correct = False
                if answer.hint: hinted = True
            elif given != answer.answer and answer.correct:
                correct = False
    return (correct, hinted)

def answers_average(answer_count, user_count):
    """
    Calculates the average of the number of answers per user.
    """

    try:
        return round(answer_count / user_count, 2)
    except ZeroDivisionError:
        raise ZeroUsersException("No users to calculate average answer count!") 

def answers_standard_distrib(user_count, answers_avg, answer_counts):
    """
    Calculates the standard distribution of the number of answers per user.
    """
    
    deviations_squared = ((ac - answers_avg) ** 2 for ac in answer_counts)
    try:
        variance = (1 / user_count) * sum(deviations_squared)
    except ZeroDivisionError:
        raise ZeroUsersException("No users to calculate standard deviation!")
    return round(math.sqrt(variance), 2)

def checkbox_exercise(exercise, users, course_inst=None):
    """
    Shows statistics on a single checkbox exercise.
    """
    
    answers = UserCheckboxExerciseAnswer.objects.filter(exercise=exercise, user__in=users)
    answer_count = answers.count()
    chosen_answers = list(answers.values_list("chosen_answers", flat=True))
    chosen_answers_set = set(chosen_answers)
    user_objects = list(answers.values_list("user", flat=True))
    users_answered = set(user_objects)
    user_count = len(users_answered)
    
    try:
        answers_avg = answers_average(answer_count, user_count)
    except ZeroUsersException:
        answers_avg = "Not enough user answers to calculate."

    user_answer_counts = (user_objects.count(user) for user in users_answered)
    try:
        answers_sd = answers_standard_distrib(user_count, answers_avg, user_answer_counts)
    except ZeroUsersException:
        answers_sd = "Not enough user answers to calculate."

    answer_data = []
    for answer in chosen_answers_set:
        choice = CheckboxExerciseAnswer.objects.get(id=answer)
        answer_data.append((choice.answer, chosen_answers.count(answer), choice.correct))
    
    correctly_by = 0
    for user in users_answered:
        evaluations = Evaluation.objects.filter(useranswer__usercheckboxexerciseanswer__exercise=exercise, useranswer__user=user)
        correct = evaluations.filter(points__gt=0.0)
        if correct: 
            correctly_by += 1

    context.update({
        "choices": choices,
        "answer_count": answer_count,
        "user_count": user_count,
        "answers_avg": answers_avg,
        "answers_sd": answers_sd,
        "answer_data": answer_data,
        "correctly_by": correctly_by,
    })
    t = loader.get_template("stats/checkbox_stats.html")
    return HttpResponse(t.render(context))

def multiple_choice_exercise(exercise, users, course_inst=None):
    """
    Shows statistics on a single multiple choice exercise.
    """
    
    answers = UserMultipleChoiceExerciseAnswer.objects.filter(exercise=content_page)
    answer_count = answers.count()
    chosen_answers = list(answers.values_list("chosen_answer", flat=True))
    chosen_answers_set = set(chosen_answers)
    user_objects = list(answers.values_list("user", flat=True))
    users_answered = set(user_objects)
    user_count = len(users_answered)
    
    try:
        answers_avg = answers_average(answer_count, user_count)
    except ZeroUsersException:
        answers_avg = "Not enough user answers to calculate."

    user_answer_counts = (user_objects.count(user) for user in users_answered)
    try:
        answers_sd = answers_standard_distrib(user_count, answers_avg, user_answer_counts)
    except ZeroUsersException:
        answers_sd = "Not enough user answers to calculate."

    answer_data = []
    for answer in chosen_answers_set:
        choice = MultipleChoiceExerciseAnswer.objects.get(id=answer)
        answer_data.append((choice.answer, chosen_answers.count(answer), choice.correct))

    correctly_by = 0
    for user in users_answered:
        evaluations = Evaluation.objects.filter(useranswer__usertextfieldexerciseanswer__exercise=content_page, useranswer__user=user)
        correct = evaluations.filter(points__gt=0.0)
        if correct: 
            correctly_by += 1

    context.update({
        "choices": choices,
        "answers": answers,
        "answer_count": answer_count,
        "user_count": user_count,
        "answers_avg": answers_avg,
        "answers_sd": answers_sd,
        "answer_data": answer_data,
        "correctly_by": correctly_by,
    })
    t = loader.get_template("stats/multiple_choice_stats.html")
    return HttpResponse(t.render(context))

def textfield_exercise(exercise, users, course_inst=None):
    """
    Shows statistics on a single textfield exercise.
    """

    answer_objects = UserTextfieldExerciseAnswer.objects.filter(exercise=content_page)
    given_answers = list(answer_objects.values_list("given_answer", flat=True))
    answer_count = len(given_answers)
    given_answers_set = set(given_answers)
    user_objects = list(answer_objects.values_list("user", flat=True))
    users_answered = set(user_objects)    
    user_count = len(users_answered)

    try:
        answers_avg = answers_average(answer_count, user_count)
    except ZeroUsersException:
        answers_avg = "Not enough user answers to calculate."

    user_answer_counts = (user_objects.count(user) for user in users_answered)
    try:
        answers_sd = answers_standard_distrib(user_count, answers_avg, user_answer_counts)
    except ZeroUsersException:
        answers_sd = "Not enough user answers to calculate."

    answer_data = []
    incorrect_sum = 0
    hinted_incorrect_sum = 0
    for answer in given_answers_set:
        count = given_answers.count(answer)
        correct, hinted = textfield_eval(answer, answers)
        if not correct:
            incorrect_sum += 1
            if hinted:
                hinted_incorrect_sum += 1
        latest = answer_objects.filter(given_answer=answer).latest('answer_date')
        answer_data.append((answer, count, correct, hinted, latest))
    answer_data = sorted(answer_data, key=lambda x: x[1], reverse=True)

    try:
        hint_coverage = hinted_incorrect_sum / incorrect_sum
    except ZeroDivisionError:
        hint_coverage = 1.0

    correctly_by = 0
    for user in users_answered:
        evaluations = Evaluation.objects.filter(useranswer__usertextfieldexerciseanswer__exercise=content_page, useranswer__user=user)
        correct = evaluations.filter(points__gt=0.0)
        if correct: 
            correctly_by += 1

    context.update({
        "answers": answers,
        "answer_count": answer_count,
        "user_count": user_count,
        "answers_avg": answers_avg,
        "answers_sd": answers_sd,
        "hint_coverage": hint_coverage,
        "answer_data": answer_data,
        "correctly_by": correctly_by,
    })
    t = loader.get_template("stats/textfield_stats.html")
    return HttpResponse(t.render(context))

def file_upload_exercise(exercise, users, course_inst=None):
    """
    Shows statistics on a single file upload exercise.
    """

    user_objects = list(UserFileUploadExerciseAnswer.objects.filter(exercise=content_page).values_list("user", flat=True))
    answer_count = len(user_objects) # how many times answered
    users_answered = set(user_objects)
    user_count = len(users_answered) # how many different users have answered

    try:
        answers_avg = answers_average(answer_count, user_count)
    except ZeroUsersException:
        answers_avg = "Not enough user answers to calculate."

    user_answer_counts = (user_objects.count(user) for user in users_answered)
    try:
        answers_sd = answers_standard_distrib(user_count, answers_avg, user_answer_counts)
    except ZeroUsersException:
        answers_sd = "Not enough user answers to calculate."

    correctly_by = 0
    for user in users_answered:
        evaluations = Evaluation.objects.filter(useranswer__userfileuploadexerciseanswer__exercise=content_page, useranswer__user=user)
        correct = evaluations.filter(points__gt=0.0)
        if correct: 
            correctly_by += 1

    context.update({
        "answer_count": answer_count,
        "user_count": user_count,
        "answers_avg": answers_avg,
        "answers_sd": answers_sd,
        "correctly_by": correctly_by,
    })
    t = loader.get_template("stats/file_upload_stats.html")
    return HttpResponse(t.render(context))

def exercise_answer_piechart(request, correct, incorrect, not_answered):
    """
    Shows statistics of correct and incorrect answers of a single exercise in a pie chart.
    """
    
    total = correct + incorrect + not_answered
    correct_pct = correct / total
    incorrect_pct = incorrect / total
    not_answered_pct = not_answered / total
    correct_deg = round(correct_pct * 360)
    incorrect_deg = round(incorrect_pct * 360)
    not_answered_deg = 360 - correct_deg - incorrect_deg
    
    bg_colors = {
        correct_deg: "lawngreen", 
        incorrect_deg: "orangered",
        not_answered_deg: "steelblue"
    }
    slice1, slice2, slice3 = sorted((correct_deg, incorrect_deg, not_answered_deg))
    bg_color1 = bg_colors[slice1]
    bg_color2 = bg_colors[slice2]
    bg_color3 = bg_colors[slice3]
    
    t = loader.get_template("stats/piechart.html")
    return t.render(RequestContext(request, {
        "bgcolor1": bg_color1,
        "bgcolor2": bg_color2,
        "bgcolor3": bg_color3,
        "slice2_start": slice1,
        "slice3_start": slice1 + slice2,
        "slice3": slice3,
        "correct_n": correct,
        "incorrect_n": incorrect,
        "not_answered_n": not_answered,
        "correct_pct": round(correct_pct * 100),
        "incorrect_pct": round(incorrect_pct * 100),
        "not_answered_pct": round(not_answered_pct * 100),
    }))

def exercise_user_answers(request, context, exercise, exercise_type_f):
    all_users = User.objects.all().order_by('username')
    courses = courses_linked(content_page)

    course_stats = []
    users = []
    for course in courses:
        users_on_course = filter_users_on_course(all_users, course)
        course_stats.append(exercise_type_f(exercise, users_on_course, course))
        users.extend(users_on_course)

    summary_stats = exercise_type_f(exercise, list(set(users)))
    context.update({
        "course_stats": course_stats,
        "summary_stats": summary_stats,
    })
    return HttpResponse(context)

    
def single_exercise(request, content_slug):
    """
    Shows statistics on a single selected task.
    """
    if not request.user.is_authenticated() and not request.user.is_active and not request.user.is_staff:
        return HttpResponseNotFound()

    exercise = ContentPage.objects.get(slug=content_slug)
    tasktype = exercise.content_type
     
    context = RequestContext(request, {
        "content": exercise,
        "tasktype": tasktype,
        "choices": exercise.get_type_object().get_choices(),
    })

    if tasktype == "CHECKBOX_EXERCISE":
        return exercise_user_answers(request, context, exercise, checkbox_exercise)
    elif tasktype == "MULTIPLE_CHOICE_EXERCISE":
        return exercise_user_answers(request, context, exercise, multiple_choice_exercise)
    elif tasktype == "TEXTFIELD_EXERCISE":
        return exercise_user_answers(request, context, exercise, textfield_exercise)
    elif tasktype == "FILE_UPLOAD_EXERCISE":
        return exercise_user_answers(request, context, exercise, file_upload_exercise)
    else:
        return HttpResponseNotFound("No stats for exercise {} found!".format(task_name))

def user_task(request, user_name, task_name):
    '''Shows a user's answers to a task.'''
    if not request.user.is_authenticated() and not request.user.is_staff:
        return HttpResponseNotFound()

    content = ContentPage.objects.get(slug=task_name)

    exercise = content_page.get_type_object()
    tasktype = content_page.content_type
    question = content.question
    choices = answers = exercise.get_choices() 

    ruser = User.objects.get(username=user_name)

    checkboxanswers = multichoiceanswers = textfieldanswers = fileanswers = None
    if tasktype == "CHECKBOX_EXERCISE":
        checkboxanswers = UserCheckboxExerciseAnswer.objects.filter(exercise=content, user=ruser)
    elif tasktype == "MULTIPLE_CHOICE_EXERCISE":
        multichoiceanswers = UserMultipleChoiceExerciseAnswer.objects.filter(exercise=content, user=ruser)
    elif tasktype == "TEXTFIELD_EXERCISE":
        textfieldanswers = UserTextfieldExerciseAnswer.objects.filter(exercise=content, user=ruser)
    elif tasktype == "FILE_UPLOAD_EXERCISE":
        fileanswers = UserFileUploadExerciseAnswer.objects.filter(exercise=content, user=ruser)

    t = loader.get_template("stats/user_task_stats.html")
    c = RequestContext(request, {
        'username': user_name,
        'taskname': task_name,
        'checkboxanswers': checkboxanswers,
        'multichoiceanswers': multichoiceanswers,
        'textfieldanswers': textfieldanswers,
        'fileanswers': fileanswers,
    })
    return HttpResponse(t.render(c))

def all_exercises(request, course_name):
    '''Shows statistics for all the tasks.'''
    if not request.user.is_authenticated() and not request.user.is_staff:
        return HttpResponseNotFound()

    tasks = ContentPage.objects.all()
    staff = User.objects.filter(is_staff=True)
    non_staff = User.objects.filter(is_staff=False)

    task_infos = []
    for task in tasks:
        taskname = task.name
        taskurl = "/" + course_name + "/" + task.slug
        
        exercise = task.get_type_object()
        tasktype = task.content_type
        question = task.question
        choices = answers = exercise.get_choices()

        if tasktype == "CHECKBOX_EXERCISE":
            all_evaluations = Evaluation.objects.filter(useranswer__usercheckboxexerciseanswer__exercise=task).exclude(useranswer__user__in=staff)
        elif tasktype == "MULTIPLE_CHOICE_EXERCISE":
            all_evaluations = Evaluation.objects.filter(useranswer__usermultiplechoiceexerciseanswer__exercise=task).exclude(useranswer__user__in=staff)
        elif tasktype == "TEXTFIELD_EXERCISE":
            all_evaluations = Evaluation.objects.filter(useranswer__usertextfieldexerciseanswer__exercise=task).exclude(useranswer__user__in=staff)
        elif tasktype == "FILE_UPLOAD_EXERCISE":
            all_evaluations = Evaluation.objects.filter(useranswer__userfileuploadexerciseanswer__exercise=task).exclude(useranswer__user__in=staff)
        else:
            continue

        total_attempts = all_evaluations.count()
        by_users = all_evaluations.values_list("useranswer__user", flat=True)
        unique_users_set = set(list(by_users))
        unique_users = len(unique_users_set)
        correct = all_evaluations.filter(points__gt=0.0).values_list("useranswer__user", flat=True)
        correct_set = set(list(correct))
        correct_by = len(correct_set)
        try:
            avg = 1.0*total_attempts/unique_users
        except ZeroDivisionError:
            avg = "N/A"

        task_infos.append((taskname, taskurl, total_attempts, unique_users, correct_by, avg))

    t = loader.get_template("stats/alltaskstats.html")
    c = RequestContext(request, {
        'course_name': course_name,
        'task_infos': task_infos,
    })
    return HttpResponse(t.render(c))

def course_users(request, course_slug, content_to_search, year, month, day):
    '''Admin view that shows a table of all users and the tasks they've done on a particular course.'''
    if not request.user.is_authenticated() and not request.user.is_active and not request.user.is_staff:
        return HttpResponseNotFound()

    selected_course = Training.objects.get(name=course_slug)
    users = User.objects.all()
    #content_nodes = selected_course.contents.all()
    #contents = [cn.content for cn in content_nodes]

    cns = ContentPage.objects.get(slug=content_to_search).content.splitlines()
    content_names = []
    for line in cns:
        mo = re.match("^\[\[\[(?P<embname>.+)\]\]\]", line)
        if mo:
            content_names.append(mo.group("embname"))
    deadline = datetime.datetime(int(year), int(month), int(day))
    contents = ContentPage.objects.filter(slug__in=content_names)
    print(content_names)

    user_evaluations = []
    for user in users:
        username = user.userprofile.student_id or user.username
        if not deadline: db_user_evaluations = Evaluation.objects.filter(useranswer__user=user, points__gt=0.0)
        else: db_user_evaluations = Evaluation.objects.filter(useranswer__user=user, points__gt=0.0, useranswer__answer_date__lt=deadline)
        evaluations = []

        print(username,)

        for content in contents:
            exercise = content.get_type_object()
            tasktype = content.content_type
            question = content.question
            choices = answers = exercise.get_choices()
            if tasktype == "CHECKBOX_EXERCISE":
                db_evaluations = db_user_evaluations.filter(useranswer__usercheckboxexerciseanswer__exercise=content)
            elif tasktype == "MULTIPLE_CHOICE_EXERCISE":
                db_evaluations = db_user_evaluations.filter(useranswer__usermultiplechoiceexerciseanswer__exercise=content)
            elif tasktype == "TEXTFIELD_EXERCISE":
                db_evaluations = db_user_evaluations.filter(useranswer__usertextfieldexerciseanswer__exercise=content)
            elif tasktype == "FILE_UPLOAD_EXERCISE":
                db_evaluations = db_user_evaluations.filter(useranswer__userfileuploadexerciseanswer__exercise=content)
            else:
                db_evaluations = []

            if db_evaluations:
                evaluations.append(1)
            else:
                evaluations.append(0)
        user_evaluations.append((username, evaluations, sum(evaluations)))

    t = loader.get_template("stats/usertable.html")
    c = RequestContext(request, {
        'course_slug':course_slug,
        'content_count':len(contents),
        'contents':contents,
        'user_evaluations':user_evaluations,
    })
    return HttpResponse(t.render(c))

def users_all(request):
    if not (request.user.is_authenticated() and request.user.is_active and\
       request.user.is_staff):
        return HttpResponseNotFound()

    users = User.objects.all().order_by('username')
    exercises = ContentPage.objects.all().exclude(content_type='LECTURE')\
                                         .order_by('name')

    # Argh...
    table_rows = [
        [user] +
        [exercise.get_type_object().get_user_evaluation(user) for exercise in exercises]
        for user in users
    ]

    t = loader.get_template("stats/users-all.html")
    c = RequestContext(request, {
        'users': users,
        'exercises': exercises,
        'table_rows': table_rows,
    })
    return HttpResponse(t.render(c))

def color_generator(total_colors):
    import colorsys
    saturation = 0.35
    value = 1.0
    for hue in range(0, 360, int(360/total_colors)):
        r, g, b = [255 * result for result in colorsys.hsv_to_rgb(hue/360, saturation, value)]
        #yield '#{:x}{:x}{:x}'.format(int(r), int(g), int(b))
        yield 'rgba({},{},{},0.65)'.format(int(r), int(g), int(b))

def users_course(request, course):
    if not (request.user.is_authenticated() and request.user.is_active and\
            request.user.is_staff):
        return HttpResponseNotFound()

    users = User.objects.all().order_by('username')
    course = Course.objects.get(slug=course)

    parent_pages = course.contents.select_related('content').order_by('ordinal_number')
    exercises = course_exercises(course)
    
    # Argh...
    table_rows = [
        [user] +
        [user_evaluation(user, e) for e in exercises]
        for user in users
    ]

    t = loader.get_template("stats/users-course.html")
    c = RequestContext(request, {
        'course': course,
        'users': users,
        'exercises': exercises,
        'table_rows': table_rows,
    })
    return HttpResponse(t.render(c))

class ZeroUsersException(Exception):
    pass
