import collections
import json
import string
import random

from django.http import HttpResponse, HttpResponseNotFound, HttpResponseForbidden,\
    HttpResponseNotAllowed, JsonResponse
from django.template import loader
from django.db import transaction, IntegrityError
from django.conf import settings

from reversion import revisions as reversion

# Other needed models
from courses.models import ContentGraph, EmbeddedLink

# The editable models
from courses.models import CourseInstance, FileUploadExercise, FileExerciseTest, FileExerciseTestStage,\
    FileExerciseTestCommand, FileExerciseTestExpectedOutput, FileExerciseTestExpectedStdout,\
    FileExerciseTestExpectedStderr, FileExerciseTestIncludeFile, IncludeFileSettings, \
    Hint, InstanceIncludeFile, InstanceIncludeFileToExerciseLink
from feedback.models import ContentFeedbackQuestion, TextfieldFeedbackQuestion, \
    ThumbFeedbackQuestion, StarFeedbackQuestion, MultipleChoiceFeedbackQuestion, \
    MultipleChoiceFeedbackAnswer

# Forms
from .forms import CreateFeedbackQuestionsForm, CreateInstanceIncludeFilesForm, CreateFileUploadExerciseForm
from .utils import get_default_lang, get_lang_list

def index(request):
    return HttpResponseNotFound()

def save_file_upload_exercise(exercise, form_data, order_hierarchy_json, old_test_ids,
                              old_stage_ids, old_cmd_ids, new_stages, new_commands):
    deletions = []
    # Collect the content page data
    #e_name = form_data['exercise_name']
    #e_content = form_data['exercise_content']
    e_default_points = form_data['exercise_default_points']
    e_tags = [tag for key, tag in sorted(form_data.items()) if key.startswith('exercise_tag')] # TODO: Do this in clean
    e_feedback_questions = form_data['exercise_feedback_questions']
    #e_question = form_data['exercise_question']
    e_manually_evaluated = form_data['exercise_manually_evaluated']
    e_ask_collaborators = form_data['exercise_ask_collaborators']
    e_allowed_filenames = form_data['exercise_allowed_filenames'].split(',') # TODO: Do this in clean

    lang_list = get_lang_list()
    for lang_code, _ in lang_list:
        e_name = form_data['exercise_name_{}'.format(lang_code)]
        setattr(exercise, 'name_{}'.format(lang_code), e_name)

        e_content = form_data['exercise_content_{}'.format(lang_code)]
        setattr(exercise, 'content_{}'.format(lang_code), e_content)

        e_question = form_data['exercise_question_{}'.format(lang_code)]
        setattr(exercise, 'question_{}'.format(lang_code), e_question)

    # TODO: Hints
    # TODO: Included files

    #exercise.name = e_name
    #exercise.content = e_content
    exercise.default_points = e_default_points
    exercise.tags = e_tags
    exercise.feedback_questions = e_feedback_questions
    #exercise.question = e_question
    exercise.manually_evaluated = e_manually_evaluated
    exercise.ask_collaborators = e_ask_collaborators
    exercise.allowed_filenames = e_allowed_filenames
    exercise.save()
    
    # Collect the test data
    test_ids = sorted(order_hierarchy_json["stages_of_tests"].keys())
    
    # Check for removed tests (existed before, but not in form data)
    for removed_test_id in sorted(old_test_ids - {int(test_id) for test_id in test_ids if not test_id.startswith('newt')}):
        print("Test with id={} was removed!".format(removed_test_id)) # TODO: Some kind of real admin logging
        removed_test = FileExerciseTest.objects.get(id=removed_test_id)
        # TODO: Reversion magic! Seems like it's taken care of automatically? Test.
        deletion = removed_test.delete()
        deletions.append(deletion)
    
    edited_tests = {}
    for test_id in test_ids:
        t_name = form_data['test_{}_name'.format(test_id)]

        # TODO: Handle the actual files first to get proper ids for new ones!
        required_files = [i.split('_') for i in form_data['test_{}_required_files'.format(test_id)]]
        t_required_ef = [int(i[1]) for i in required_files if i[0] == 'ef']
        t_required_if = [int(i[1]) for i in required_files if i[0] == 'if']
                
        # Check for new tests
        if test_id.startswith('newt'):
            current_test = FileExerciseTest()
            current_test.exercise = exercise
        else:
            # Check for existing tests that are part of this exercise's suite
            current_test = FileExerciseTest.objects.get(id=int(test_id))

        # Set the test values
        current_test.name = t_name
        current_test.save() # Needed for the required files
        current_test.required_files = t_required_ef
        current_test.required_instance_files = t_required_if

        # Save the test and store a reference
        current_test.save()
        edited_tests[test_id] = current_test

    # Collect the stage data
    # Deferred constraints: https://code.djangoproject.com/ticket/20581
    for removed_stage_id in sorted(old_stage_ids - {int(stage_id) for stage_id in new_stages.keys() if not stage_id.startswith('news')}):
        print("Stage with id={} was removed!".format(removed_stage_id))
        try:
            removed_stage = FileExerciseTestStage.objects.get(id=removed_stage_id)
        except FileExerciseTestStage.DoesNotExist:
            pass # Probably taken care of by test deletion cascade
        # TODO: Reversion magic!
        else:
            deletion = removed_stage.delete()
            deletions.append(deletion)

    stage_count = len(new_stages)
    edited_stages = {}
    for stage_id, stage_info in new_stages.items():
        s_depends_on = form_data['stage_{}_depends_on'.format(stage_id)]

        if stage_id.startswith('news'):
            current_stage = FileExerciseTestStage()
        else:
            current_stage = FileExerciseTestStage.objects.get(id=int(stage_id))

        for lang_code, _ in lang_list:
            s_name = form_data['stage_{}_name_{}'.format(stage_id, lang_code)]
            setattr(current_stage, 'name_{}'.format(lang_code), s_name)

        current_stage.test = edited_tests[stage_info.test]
        current_stage.depends_on = s_depends_on
        current_stage.ordinal_number = stage_info.ordinal_number + stage_count + 1 # Note

        current_stage.save()
        edited_stages[stage_id] = current_stage

    # HACK: Workaround for lack of deferred constraints on unique_together
    for stage_id, stage_obj in edited_stages.items():
        stage_obj.ordinal_number -= stage_count + 1
        stage_obj.save()
        
    # Collect the command data
    for removed_command_id in sorted(old_cmd_ids - {int(command_id) for command_id in new_commands.keys() if not command_id.startswith('newc')}):
        print("Command with id={} was removed!".format(removed_command_id))
        try:
            removed_command = FileExerciseTestCommand.objects.get(id=removed_command_id)
        except FileExerciseTestCommand.DoesNotExist:
            pass # Probably taken care of by test or stage deletion cascade
            # TODO: Reversion magic!
        else:
            deletion = removed_command.delete()
            deletions.append(deletion)

    print("Total deletions: {}".format(repr(deletions)))

    command_count = len(new_commands)
    edited_commands = {}
    for command_id, command_info in new_commands.items():
        c_significant_stdout = form_data['command_{}_significant_stdout'.format(command_id)]
        c_significant_stderr = form_data['command_{}_significant_stderr'.format(command_id)]
        c_return_value = form_data['command_{}_return_value'.format(command_id)]
        c_timeout = form_data['command_{}_timeout'.format(command_id)]

        if command_id.startswith('newc'):
            current_command = FileExerciseTestCommand()
        else:
            current_command = FileExerciseTestCommand.objects.get(id=int(command_id))

        for lang_code, _ in lang_list:
            c_command_line = form_data['command_{}_command_line_{}'.format(command_id, lang_code)]
            c_input_text = form_data['command_{}_input_text_{}'.format(command_id, lang_code)]
            setattr(current_command, 'command_line_{}'.format(lang_code), c_command_line)
            setattr(current_command, 'input_text_{}'.format(lang_code), c_input_text)

        current_command.stage = edited_stages[command_info.stage]
        current_command.significant_stdout = c_significant_stdout
        current_command.significant_stderr = c_significant_stderr
        current_command.return_value = c_return_value
        current_command.timeout = c_timeout
        current_command.ordinal_number = command_info.ordinal_number + command_count + 1 # Note

        current_command.save()
        edited_commands[command_id] = current_command

    # HACK: Workaround for lack of deferred constraints on unique_together
    for command_id, command_obj in edited_commands.items():
        command_obj.ordinal_number -= command_count + 1
        command_obj.save()
            
    
        
Stage = collections.namedtuple('Stage', ['test', 'ordinal_number'])
Command = collections.namedtuple('Command', ['stage', 'ordinal_number'])

# We need the following urls, at least:
# fileuploadexercise/add
# fileuploadexercise/{id}/change
# fileuploadexercise/{id}/delete
def file_upload_exercise(request, exercise_id=None, action=None):
    # Admins only, consider @staff_member_required
    if not (request.user.is_staff and request.user.is_authenticated() and request.user.is_active):
        return HttpResponseForbidden("Only admins are allowed to edit file upload exercises.")

    # GET = show the page
    # POST = validate & save the submitted form

    # TODO: All that stuff in admin which allows the user to upload new things etc.

    # TODO: How to handle the creation of new exercises? 

    # Get the exercise
    try:
        exercise = FileUploadExercise.objects.get(id=exercise_id)
    except FileUploadExercise.DoesNotExist as e:
        #pass # DEBUG
        return HttpResponseNotFound("File upload exercise with id={} not found.".format(exercise_id))

    # Get the configurable hints linked to this exercise
    hints = Hint.objects.filter(exercise=exercise)

    # Get the exercise specific files
    include_files = FileExerciseTestIncludeFile.objects.filter(exercise=exercise)
    
    # TODO: Get the instance specific files
    # 1. scan the content graphs and embedded links to find out, if this exercise is linked
    #    to an instance. we need a manytomany relation here, that is instance specific
    # 2. get the files and show a pool of them
    instance_files = InstanceIncludeFile.objects.all() # TODO: This is debug code
    instance_file_links = InstanceIncludeFileToExerciseLink.objects.filter(exercise=exercise)
    instances = [{"id" : instance.id, "name" : instance.name} for instance in CourseInstance.objects.all()]
    
    tests = FileExerciseTest.objects.filter(exercise=exercise_id).order_by("name")
    test_list = []
    stages = None
    commands = None
    for test in tests:
        stages = FileExerciseTestStage.objects.filter(test=test).order_by("ordinal_number")
        stage_list = []
        for stage in stages:
            cmd_list = []
            commands = FileExerciseTestCommand.objects.filter(stage=stage).order_by("ordinal_number")
            for cmd in commands:
                expected_outputs = FileExerciseTestExpectedOutput.objects.filter(command=cmd).order_by("ordinal_number")
                cmd_list.append((cmd, expected_outputs))
            stage_list.append((stage, cmd_list))
        test_list.append((test, stage_list))

    # TODO: Save the additions, removals and editions sent by the user 
    if request.method == "POST":
        form_contents = request.POST
        uploaded_files = request.FILES

        #print(form_contents)
        print("POST key-value pairs:")
        for k, v in sorted(form_contents.lists()):
            if k == "order_hierarchy":
                order_hierarchy_json = json.loads(v[0])
                print("order_hierarchy:")
                print(json.dumps(order_hierarchy_json, indent=4))
            else:
                print("{}: '{}'".format(k, v))

        print(uploaded_files)
        new_stages = {}
        for test_id, stage_list in order_hierarchy_json['stages_of_tests'].items():
            for i, stage_id in enumerate(stage_list):
                new_stages[stage_id] = Stage(test=test_id, ordinal_number=i+1)

        new_commands = {}
        for stage_id, command_list in order_hierarchy_json['commands_of_stages'].items():
            for i, command_id in enumerate(command_list):
                new_commands[command_id] = Command(stage=stage_id, ordinal_number=i+1)

        old_test_ids = set(tests.values_list('id', flat=True))
        if stages is not None:
            old_stage_ids = set(stages.values_list('id', flat=True))
        else:
            old_stage_ids = set()
        if commands is not None:
            old_cmd_ids = set(commands.values_list('id', flat=True))
        else:
            old_cmd_ids = set()

        data = request.POST.copy()
        data.pop("csrfmiddlewaretoken")
        tag_fields = [k for k in data.keys() if k.startswith("exercise_tag")]

        form = CreateFileUploadExerciseForm(tag_fields, order_hierarchy_json, data)

        if form.is_valid():
            print("DEBUG: the form is valid")
            cleaned_data = form.cleaned_data

            # create/update the form
            try:
                with transaction.atomic(), reversion.create_revision():
                    save_file_upload_exercise(exercise, cleaned_data, order_hierarchy_json,
                                              old_test_ids, old_stage_ids, old_cmd_ids,
                                              new_stages, new_commands)
                    reversion.set_user(request.user)
                    reversion.set_comment(cleaned_data['version_comment'])
            except IntegrityError as e:
                # TODO: Do something useful
                raise e
            
            return JsonResponse({
                "yeah!": "everything went ok",
            })
        else:
            print("DEBUG: the form is not valid")
            print(form.errors)
            return JsonResponse({
                "error": form.errors,
            })
    
    t = loader.get_template("exercise_admin/file-upload-exercise-{action}.html".format(action=action))
    c = {
        'exercise': exercise,
        'hints': hints,
        'instances': instances,
        'include_files': include_files,
        'instance_files': instance_files,
        'instance_file_links': instance_file_links,
        'tests': test_list,

    }
    return HttpResponse(t.render(c, request))

def get_feedback_questions(request):
    if not (request.user.is_staff and request.user.is_authenticated() and request.user.is_active):
        return JsonResponse({
            "error": "Only logged in admins can query feedback questions!"
        })

    feedback_questions = ContentFeedbackQuestion.objects.all()
    result = []
    for question in feedback_questions:
        question = question.get_type_object()
        question_json = {
            "id": question.id,
            "question" : question.question,
            "type" : question.question_type,
            "readable_type": question.get_human_readable_type(),
            "choices": [],
        }
        if question.question_type == "MULTIPLE_CHOICE_FEEDBACK":
            question_json["choices"] = [choice.answer for choice in question.get_choices()]
        result.append(question_json)

    return JsonResponse({
        "result": result
    })

def edit_feedback_questions(request):
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])

    if not (request.user.is_staff and request.user.is_authenticated() and request.user.is_active):
        return JsonResponse({
            "error" : {
                "__all__" : {
                    "message" : "Only logged in users can edit feedback questions!",
                    "code" : "authentication"
                }
            }
        })

    data = request.POST.dict()
    data.pop("csrfmiddlewaretoken")

    feedback_questions = ContentFeedbackQuestion.objects.all()
    form = CreateFeedbackQuestionsForm(feedback_questions, data)
    
    if form.is_valid():
        # Edit existing feedback questions if necessary
        cleaned_data = form.cleaned_data
        for q_obj in feedback_questions:
            q_obj = q_obj.get_type_object()
            question = cleaned_data["question_field_[{}]".format(q_obj.id)]
            choice_prefix = "choice_field_[{}]".format(q_obj.id)
            choice_keys = sorted([k for (k, v) in cleaned_data.items() if k.startswith(choice_prefix) and v])

            if q_obj.question != question:
                q_obj.question = question
                q_obj.save()
            if q_obj.question_type == "MULTIPLE_CHOICE_FEEDBACK":
                existing_choices = q_obj.get_choices()
                existing_choices_len = len(existing_choices)
                for i, k in enumerate(choice_keys):
                    choice = cleaned_data[k]
                    if existing_choices_len <= i:
                        MultipleChoiceFeedbackAnswer(question=q_obj, answer=choice).save()
                    elif choice not in [choice.answer for choice in existing_choices]:
                        choice_obj = existing_choices[i]
                        choice_obj.answer = choice
                        choice_obj.save()
                        
        # Add new feedback questions
        new_feedback_count = len([k for k in cleaned_data if k.startswith("question_field_[new")])
        for i in range(new_feedback_count):
            id_new = "new-{}".format(i + 1)
            question = cleaned_data["question_field_[{}]".format(id_new)]
            question_type = cleaned_data["type_field_[{}]".format(id_new)]
            choice_prefix = "choice_field_[{}]".format(id_new)
            choices = [v for (k, v) in cleaned_data.items() if k.startswith(choice_prefix) and v]
            
            if question_type == "THUMB_FEEDBACK":
                q_obj = ThumbFeedbackQuestion(question=question)
                q_obj.save()
            elif question_type == "STAR_FEEDBACK":
                q_obj = StarFeedbackQuestion(question=question)
                q_obj.save()
            elif question_type == "MULTIPLE_CHOICE_FEEDBACK":
                q_obj = MultipleChoiceFeedbackQuestion(question=question)
                q_obj.save()
                for choice in choices:
                    MultipleChoiceFeedbackAnswer(question=q_obj, answer=choice).save()
            elif question_type == "TEXTFIELD_FEEDBACK":
                q_obj = TextfieldFeedbackQuestion(question=question)
                q_obj.save()
    else:
        return JsonResponse({
            "error" : form.errors
        })
    
    return get_feedback_questions(request)

def get_instance_files(request, exercise_id):
    if not (request.user.is_staff and request.user.is_authenticated() and request.user.is_active):
        return JsonResponse({
            "error": "Only logged in admins can query instance files!"
        })
    
    instance_files = InstanceIncludeFile.objects.all()

    result = []
    for instance_file in instance_files:
        try:
            link = InstanceIncludeFileToExerciseLink.objects.get(include_file=instance_file, exercise=exercise_id)
            link_json = {
                "id" : link.id,
                "names" : {},
                "purpose" : link.file_settings.purpose,
                "purpose_display" : link.file_settings.get_purpose_display(),
                "chown_settings" : link.file_settings.chown_settings,
                "chgrp_settings" : link.file_settings.chgrp_settings,
                "chmod_settings" : link.file_settings.chmod_settings,
            }
        except InstanceIncludeFileToExerciseLink.DoesNotExist:
            link = None
            link_json = {}
        instance_file_json = {
            "id" : instance_file.id,
            "instance" : instance_file.instance.name,
            "default_names" : {},
            "descriptions" : {},
            "urls" : {},
            "link" : link_json,
        }
        lang_list = get_lang_list()
        for lang_code, _ in lang_list:
            default_name_attr = "default_name_{}".format(lang_code)
            description_attr = "description_{}".format(lang_code)
            fileinfo_attr = "fileinfo_{}".format(lang_code)
            name_attr = "name_{}".format(lang_code)
            try:
                url = getattr(instance_file, fileinfo_attr).url
            except ValueError:
                url = ""
            instance_file_json["urls"][lang_code] = url
            instance_file_json["default_names"][lang_code] = getattr(instance_file, default_name_attr) or ""
            instance_file_json["descriptions"][lang_code] = getattr(instance_file, description_attr) or ""
            if link is not None:
                instance_file_json["link"]["names"][lang_code] = getattr(link.file_settings, name_attr) or ""
        result.append(instance_file_json)

    default_lang = get_default_lang()
    return JsonResponse({
        "result": sorted(result, key=lambda f: f["default_names"][default_lang])
    })

# HACK: Workaround for lack of deferred constraints on unique_together
def create_placeholder_name(placeholder_names, existing_names):
    PLACEHOLDER_NAME_LEN = 10
    PLACEHOLDER_NAME_CHARS = string.ascii_uppercase + string.digits
    while True:
        placeholder_name = "".join(random.choice(PLACEHOLDER_NAME_CHARS) for _ in range(PLACEHOLDER_NAME_LEN))
        if placeholder_name not in placeholder_names and placeholder_name not in existing_names:
            return placeholder_name

def edit_instance_files(request, exercise_id):
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])

    if not (request.user.is_staff and request.user.is_authenticated() and request.user.is_active):
        return JsonResponse({
            "error" : {
                "__all__" : {
                    "message" : "Only logged in users can edit instance files!",
                    "code" : "authentication"
                }
            }
        })

    data = request.POST.dict()
    data.pop("csrfmiddlewaretoken")
    files = request.FILES.dict()

    new_file_id_str = data.pop("new_instance_files")
    if new_file_id_str:
        new_file_ids = new_file_id_str.split(",")
    else:
        new_file_ids = []
    linked_file_id_str = data.pop("linked_files")
    if linked_file_id_str:
        linked_file_ids = linked_file_id_str.split(",")
    else:
        linked_file_ids = []

    instance_files = InstanceIncludeFile.objects.all()
    instance_file_links = InstanceIncludeFileToExerciseLink.objects.filter(exercise=exercise_id)
    form = CreateInstanceIncludeFilesForm(instance_files, new_file_ids, linked_file_ids, data, files)

    if form.is_valid():
        cleaned_data = form.cleaned_data
        lang_list = get_lang_list()
        
        edited_default_names = {}
        default_names = {lang_code : [getattr(instance_file, "default_name_{}".format(lang_code))
                                      for instance_file in instance_files]
                         for lang_code, _ in lang_list}

        # Edit existing instance files
        for instance_file in instance_files:
            file_changed = False
            for lang_code, _ in lang_list:
                fileinfo = cleaned_data.get("instance_file_file_[{id}]_{lang}".format(id=instance_file.id, lang=lang_code))
                default_name = cleaned_data.get("instance_file_default_name_[{id}]_{lang}".format(id=instance_file.id, lang=lang_code))
                description = cleaned_data.get("instance_file_description_[{id}]_{lang}".format(id=instance_file.id, lang=lang_code))

                if instance_file.default_name != default_name:
                    placeholder_name = create_placeholder_name(edited_default_names.keys(), default_names[lang_code])
                    setattr(instance_file, "default_name_{}".format(lang_code), placeholder_name)
                    edited_default_names[placeholder_name] = (default_name, instance_file, lang_code)
                    file_changed = True
                if fileinfo is not None:
                    setattr(instance_file, "fileinfo_{}".format(lang_code), fileinfo)
                    file_changed = True
                if description is not None and instance_file.description != description:
                    setattr(instance_file, "description_{}".format(lang_code), description)
                    file_changed = True

            instance_id = cleaned_data.get("instance_file_instance_[{id}]".format(id=instance_file.id))
            if str(instance_file.instance.id) != instance_id:
                instance_file.instance_id = instance_id
                file_changed = True

            if file_changed:
                instance_file.save()

        # Replace placeholder default names with actual default names
        for default_name, instance_file, lang_code in edited_default_names.values():
            setattr(instance_file, "default_name_{}".format(lang_code), default_name)
            instance_file.save()

        edited_names = {}
        names = {lang_code : [getattr(instance_file_link.file_settings, "name_{}".format(lang_code))
                              for instance_file_link in instance_file_links]
                 for lang_code, _ in lang_list}
        already_linked_file_ids = []

        # Remove or edit existing instance file links
        for instance_file_link in instance_file_links:
            file_id = str(instance_file_link.include_file.id)
            if file_id not in linked_file_ids:
                instance_file_link.delete()
            else:
                file_changed = False
                already_linked_file_ids.append(file_id)
                
                for lang_code, _ in lang_list:
                    name = cleaned_data.get("instance_file_name_[{id}]_{lang}".format(id=file_id, lang=lang_code))
                    if instance_file_link.file_settings.name != name:
                        placeholder_name = create_placeholder_name(edited_names.keys(), names[lang_code])
                        setattr(instance_file_link.file_settings, "name_{}".format(lang_code), placeholder_name)
                        edited_names[placeholder_name] = (name, instance_file_link, lang_code)
                        file_changed = True

                purpose = cleaned_data.get("instance_file_purpose_[{id}]".format(id=file_id))
                chown = cleaned_data.get("instance_file_chown_[{id}]".format(id=file_id))
                chgrp = cleaned_data.get("instance_file_chgrp_[{id}]".format(id=file_id))
                chmod = cleaned_data.get("instance_file_chmod_[{id}]".format(id=file_id))

                if purpose is not None and instance_file_link.file_settings.purpose != purpose:
                    instance_file_link.file_settings.purpose = purpose
                    file_changed = True
                if chown is not None and instance_file_link.file_settings.chown_settings != chown:
                    instance_file_link.file_settings.chown_settings = chown
                    file_changed = True
                if chgrp is not None and instance_file_link.file_settings.chgrp_settings != chgrp:
                    instance_file_link.file_settings.chgrp_settings = chgrp
                    file_changed = True
                if chmod is not None and instance_file_link.file_settings.chmod_settings != chmod:
                    instance_file_link.file_settings.chmod_settings = chmod
                    file_changed = True

            if file_changed:
                instance_file_link.file_settings.save()

        # Replace placeholder names with actual names
        for name, instance_file_link, lang_code in edited_names.values():
            setattr(instance_file_link.file_settings, "name_{}".format(lang_code), name)
            instance_file_link.file_settings.save()
            
        new_instance_files = {}

        # Create new instance files
        for file_id in new_file_ids:
            instance_file = InstanceIncludeFile()
            for lang_code, _ in lang_list:
                fileinfo_field = "instance_file_[{id}]_{lang}".format(id=file_id, lang=lang_code)
                default_name_field = "instance_file_default_name_[{id}]_{lang}".format(id=file_id, lang=lang_code)
                description_field = "instance_file_description_[{id}]_{lang}".format(id=file_id, lang=lang_code)
                setattr(instance_file, "fileinfo_{}".format(lang_code), cleaned_data.get(fileinfo_field))
                setattr(instance_file, "default_name_{}".format(lang_code), cleaned_data.get(default_name_field))
                setattr(instance_file, "description_{}".format(lang_code), cleaned_data.get(description_field))
            instance_field = "instance_file_instance_[{id}]".format(id=file_id)
            instance_file.instance_id = cleaned_data.get(instance_field)
            instance_file.save()
            new_instance_files[file_id] = instance_file.id

        # Create new instance file links
        new_linked_file_ids = [file_id for file_id in linked_file_ids if file_id not in already_linked_file_ids]
        for file_id in new_linked_file_ids:
            file_settings = IncludeFileSettings()
            instance_file_link = InstanceIncludeFileToExerciseLink()
            for lang_code, _ in lang_list:
                name_field = "instance_file_name_[{id}]_{lang}".format(id=file_id, lang=lang_code)
                setattr(file_settings, "name_{}".format(lang_code), cleaned_data.get(name_field))
            purpose_field = "instance_file_purpose_[{id}]".format(id=file_id)
            chown_field = "instance_file_chown_[{id}]".format(id=file_id)
            chgrp_field = "instance_file_chgrp_[{id}]".format(id=file_id)
            chmod_field = "instance_file_chmod_[{id}]".format(id=file_id)
            file_settings.purpose = cleaned_data.get(purpose_field)
            file_settings.chown_settings = cleaned_data.get(chown_field)
            file_settings.chgrp_settings = cleaned_data.get(chgrp_field)
            file_settings.chmod_settings = cleaned_data.get(chmod_field)
            file_settings.save()
            instance_file_link.exercise_id = exercise_id
            if file_id.startswith("new"):
                file_id = new_instance_files[file_id]
            instance_file_link.include_file_id = int(file_id)
            instance_file_link.file_settings = file_settings
            instance_file_link.save()

    else:
        return JsonResponse({
            "error" : form.errors
        })
    
    return get_instance_files(request, exercise_id)
