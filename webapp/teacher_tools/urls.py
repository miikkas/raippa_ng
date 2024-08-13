from django.urls import path

from . import views

app_name = "teacher_tools"

urlpatterns = [
    path(
        "<course:course>/<instance:instance>/search_records/",
        views.search_records,
        name="search_records",
    ),
    path(
        "<course:course>/<instance:instance>/<content:content>/download_answers/",
        views.download_answers,
        name="download_answers",
    ),
    path(
        "<course:course>/<instance:instance>/<content:content>/answer_summary/",
        views.answer_summary,
        name="answer_summary",
    ),
    path(
        "<course:course>/<instance:instance>/<content:content>/batch_grade/",
        views.batch_grade_task,
        name="batch_grade",
    ),
    path(
        "<course:course>/<instance:instance>/<content:content>/reset_completion/",
        views.reset_completion,
        name="reset_completion",
    ),
    path(
        "<course:course>/<instance:instance>/enrollments/",
        views.manage_enrollments,
        name="manage_enrollments",
    ),
    path(
        "<course:course>/<instance:instance>/records/<user:user>",
        views.transfer_records,
        name="transfer_records",
    ),
    path(
        "<course:course>/<instance:instance>/completion/<user:user>/",
        views.student_course_completion,
        name="student_completion",
    ),
    path(
        "<course:course>/<instance:instance>/completion/",
        views.course_completion,
        name="completion",
    ),
    path(
        "<course:course>/<instance:instance>/completion-csv/",
        views.course_completion_csv,
        name="completion_csv",
    ),
    path(
        "<course:course>/<instance:instance>/completion/grades/",
        views.calculate_grades,
        name="request_grades",
    ),
    path(
        "<course:course>/<instance:instance>/completion-csv/progress/<slug:task_id>/",
        views.course_completion_csv_progress,
        name="completion_csv_progress",
    ),
    path(
        "<course:course>/<instance:instance>/completion-csv/download/<slug:task_id>/",
        views.course_completion_csv_download,
        name="completion_csv_download",
    ),
    path(
        "<course:course>/<instance:instance>/reminders/load/",
        views.load_reminders,
        name="load_reminders",
    ),
    path(
        "<course:course>/<instance:instance>/reminders/discard/",
        views.discard_reminders,
        name="discard_reminders",
    ),
    path(
        "<course:course>/<instance:instance>/reminders/progress/<slug:task_id>/",
        views.reminders_progress,
        name="reminders_progress",
    ),
    path(
        "<course:course>/<instance:instance>/reminders/",
        views.manage_reminders,
        name="reminders",
    ),
    path(
        "<course:course>/<instance:instance>/<content:content>/plagiarism/",
        views.exercise_plagiarism,
        name="exercise_plagiarism",
    ),
    path(
        "<course:course>/<instance:instance>/<content:content>/plagiarism/progress/<slug:task_id>/",
        views.moss_progress,
        name="moss_progress",
    ),
    path(
        "<course:course>/<instance:instance>/exemptions/",
        views.manage_exemptions,
        name="exemptions",
    ),
    path(
        "<course:course>/<instance:instance>/create_exemption/",
        views.create_exemption,
        name="create_exemption",
    ),
    path(
        "<course:course>/<instance:instance>/delete_exemption/<user:user>/<int:graph_id>/",
        views.delete_exemption,
        name="delete_exemption",
    ),
 ]
