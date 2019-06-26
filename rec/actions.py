"""
Built-in, globally-available rec actions.
"""

from django.contrib import messages
from rec import helpers
from rec.utils import model_ngettext
from django.core.exceptions import PermissionDenied
from django.template.response import TemplateResponse
from django.utils.translation import gettext as _, gettext_lazy


def delete_selected(modelrec, request, queryset):
    """
    Default action which deletes the selected objects.

    This action first displays a confirmation page which shows all the
    deletable objects, or, if the user has no permission one of the related
    childs (foreignkeys), a "permission denied" message.

    Next, it deletes all selected objects and redirects back to the change list.
    """
    opts = modelrec.model._meta
    app_label = opts.app_label

    # Populate deletable_objects, a data structure of all related objects that
    # will also be deleted.
    deletable_objects, model_count, perms_needed, protected = modelrec.get_deleted_objects(queryset, request)

    # The user has already confirmed the deletion.
    # Do the deletion and return None to display the change list view again.
    if request.POST.get('post') and not protected:
        if perms_needed:
            raise PermissionDenied
        n = queryset.count()
        if n:
            for obj in queryset:
                obj_display = str(obj)
                modelrec.log_deletion(request, obj, obj_display)
            modelrec.delete_queryset(request, queryset)
            modelrec.message_user(request, _("Successfully deleted %(count)d %(items)s.") % {
                "count": n, "items": model_ngettext(modelrec.opts, n)
            }, messages.SUCCESS)
        # Return None to display the change list page again.
        return None

    objects_name = model_ngettext(queryset)

    if perms_needed or protected:
        title = _("Cannot delete %(name)s") % {"name": objects_name}
    else:
        title = _("Are you sure?")

    context = {
        **modelrec.rec_site.each_context(request),
        'title': title,
        'objects_name': str(objects_name),
        'deletable_objects': [deletable_objects],
        'model_count': dict(model_count).items(),
        'queryset': queryset,
        'perms_lacking': perms_needed,
        'protected': protected,
        'opts': opts,
        'action_checkbox_name': helpers.ACTION_CHECKBOX_NAME,
        'media': modelrec.media,
    }

    request.current_app = modelrec.rec_site.name

    # Display the confirmation page
    return TemplateResponse(request, modelrec.delete_selected_confirmation_template or [
        "rec/%s/%s/delete_selected_confirmation.html" % (app_label, opts.model_name),
        "rec/%s/delete_selected_confirmation.html" % app_label,
        "rec/delete_selected_confirmation.html"
    ], context)


delete_selected.allowed_permissions = ('delete',)
delete_selected.short_description = gettext_lazy("Delete selected %(verbose_name_plural)s")
