from django import template
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext as _

from courses.models import default_fue_timeout

from ..utils import get_lang_list

register = template.Library()

@register.inclusion_tag('exercise_admin/file-upload-exercise-test-tab.html')
def test_tab(test_obj, stages_list, jstemplate=False):
    if not jstemplate:
        return {'test': test_obj, 'stages': stages_list,}

    lang_list = get_lang_list()

    class TemplateCommand:
        id = "SAMPLE_COMMAND_ID"
        ordinal_number = "SAMPLE_COMMAND_ORDINAL_NUMBER"
        #command_line = "New command"
        timeout = default_fue_timeout()

        def __init__(self):
            for lang_code, lang_name in lang_list:
                setattr(self, 'command_line_{}'.format(lang_code), "New command ({})".format(lang_name))
                setattr(self, 'input_text_{}'.format(lang_code), "")

    class TemplateStage:
        id = "SAMPLE_STAGE_ID"
        ordinal_number = "SAMPLE_STAGE_ORDINAL_NUMBER"
        #name = "New stage"

        def __init__(self):
            for lang_code, _ in lang_list:
                setattr(self, 'name_{}'.format(lang_code), "New stage")

    class TemplateTest:
        id = "SAMPLE_TEST_ID"
        name = "New test"

    return {'test': TemplateTest(), 'stages': [(TemplateStage(), [(TemplateCommand(), [])])]}

@register.inclusion_tag('exercise_admin/file-upload-exercise-include-file-tr.html')
def include_file_tr(include_file, jstemplate=False):
    if not jstemplate:
        return {'include_file': include_file,}

    lang_list = get_lang_list()

    class FileSettings:
        purpose = "SAMPLE_PURPOSE"
        get_purpose_display = "SAMPLE_GET_PURPOSE_DISPLAY"
        chown_settings = "SAMPLE_CHOWN_SETTINGS"
        chgrp_settings = "SAMPLE_CHGRP_SETTINGS"
        
        def __init__(self):
            for lang_code, _ in lang_list:
                setattr(self, 'name_{}'.format(lang_code), "SAMPLE_NAME_{}".format(lang_code))

    class IncludeFile:
        id = "SAMPLE_ID"
        file_settings = FileSettings()

        def __init__(self):
            for lang_code, _ in lang_list:
                setattr(self, 'description_{}'.format(lang_code), "SAMPLE_DESCRIPTION_{}".format(lang_code))

    return {'include_file' : IncludeFile()}

@register.inclusion_tag('exercise_admin/file-upload-exercise-include-file-popup.html')
def include_file_popup(include_file, create=False, jstemplate=False):
    if not jstemplate:
        return {
            'include_file': include_file,
            'create' : create,
        }
    lang_list = get_lang_list()

    class FileSettings:
        chmod_settings = "rw-rw-rw-"
        
        def __init__(self):
            for lang_code, _ in lang_list:
                setattr(self, 'name_{}'.format(lang_code), "")

    class FileInfo:
        url = None
    
    class IncludeFile:
        id = "SAMPLE_ID"
        file_settings = FileSettings()
        
        def __init__(self):
            for lang_code, _ in lang_list:
                setattr(self, 'default_name_{}'.format(lang_code), "")
                setattr(self, 'description_{}'.format(lang_code), "")
                setattr(self, 'fileinfo_{}'.format(lang_code), FileInfo())

    return {
        'include_file' : IncludeFile(),
        'create' : create,
    }

@register.inclusion_tag('exercise_admin/file-upload-exercise-edit-instance-file.html')
def edit_instance_file(create):
    if create:
        file_id = "SAMPLE_ID_CREATE"
    else:
        file_id = "SAMPLE_ID"
    return {
        "file_id" : file_id,
        "file_default_name" : "SAMPLE_DEFAULT_NAME",
        "file_description" : "SAMPLE_DESCRIPTION",
        "create" : create
    }

@register.inclusion_tag('exercise_admin/file-upload-exercise-edit-file-link.html')
def edit_instance_file_link(linked):
    if linked:
        file_id = "SAMPLE_ID_LINKED"
    else:
        file_id = "SAMPLE_ID"
    return {
        "file_id" : file_id,
        "file_name" : "SAMPLE_NAME",
        "file_purpose" : "SAMPLE_PURPOSE",
        "file_chown_settings" : "SAMPLE_CHOWN_SETTINGS",
        "file_chgrp_settings" : "SAMPLE_CHGRP_SETTINGS",
        "file_chmod_settings" : "SAMPLE_CHMOD_SETTINGS",
        "linked" : linked
    }

@register.inclusion_tag('exercise_admin/file-upload-exercise-instance-file-popup-tr.html')
def instance_file_popup_tr(linked):
    if linked:
        file_id = "SAMPLE_ID_LINKED"
    else:
        file_id = "SAMPLE_ID"
    return {
        "file_id" : file_id,
        "file_default_name" : "SAMPLE_DEFAULT_NAME",
        "file_description" : "SAMPLE_DESCRIPTION",
        "linked" : linked,
    }

@register.simple_tag()
def lang_reminder(lang_code):
    s = '<span class="language-code-reminder" title="The currently selected translation">{}</span>'.format(lang_code)
    return mark_safe(s)

@register.simple_tag()
def get_translated_field(model, variable, lang_code):
    if model:
        return getattr(model, '{}_{}'.format(variable, lang_code))
    else:
        return ''
