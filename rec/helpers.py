import json

from django import forms
from django.conf import settings
from rec.utils import (
    display_for_field, flatten_fieldsets, help_text_for_field, label_for_field,
    lookup_field,
)
from django.core.exceptions import ObjectDoesNotExist
from django.db.models.fields.related import ManyToManyRel
from django.forms.utils import flatatt
from django.template.defaultfilters import capfirst, linebreaksbr
from django.utils.html import conditional_escape, format_html
from django.utils.safestring import mark_safe
from django.utils.translation import gettext, gettext_lazy as _

ACTION_CHECKBOX_NAME = '_selected_action'


class ActionForm(forms.Form):
    action = forms.ChoiceField(label=_('Action:'))
    select_across = forms.BooleanField(
        label='',
        required=False,
        initial=0,
        widget=forms.HiddenInput({'class': 'select-across'}),
    )


checkbox = forms.CheckboxInput({'class': 'action-select'}, lambda value: False)


class RecForm:
    def __init__(self, form, fieldsets, prepopulated_fields, readonly_fields=None, model_rec=None):
        self.form, self.fieldsets = form, fieldsets
        self.prepopulated_fields = [{
            'field': form[field_name],
            'dependencies': [form[f] for f in dependencies]
        } for field_name, dependencies in prepopulated_fields.items()]
        self.model_rec = model_rec
        if readonly_fields is None:
            readonly_fields = ()
        self.readonly_fields = readonly_fields

    def __iter__(self):
        for name, options in self.fieldsets:
            yield Fieldset(
                self.form, name,
                readonly_fields=self.readonly_fields,
                model_rec=self.model_rec,
                **options
            )

    @property
    def errors(self):
        return self.form.errors

    @property
    def non_field_errors(self):
        return self.form.non_field_errors

    @property
    def media(self):
        media = self.form.media
        for fs in self:
            media = media + fs.media
        return media


class Fieldset:
    def __init__(self, form, name=None, readonly_fields=(), fields=(), classes=(),
                 description=None, model_rec=None):
        self.form = form
        self.name, self.fields = name, fields
        self.classes = ' '.join(classes)
        self.description = description
        self.model_rec = model_rec
        self.readonly_fields = readonly_fields

    @property
    def media(self):
        if 'collapse' in self.classes:
            extra = '' if settings.DEBUG else '.min'
            return forms.Media(js=['rec/js/collapse%s.js' % extra])
        return forms.Media()

    def __iter__(self):
        for field in self.fields:
            yield Fieldline(self.form, field, self.readonly_fields, model_rec=self.model_rec)


class Fieldline:
    def __init__(self, form, field, readonly_fields=None, model_rec=None):
        self.form = form  # A django.forms.Form instance
        if not hasattr(field, "__iter__") or isinstance(field, str):
            self.fields = [field]
        else:
            self.fields = field
        self.has_visible_field = not all(
            field in self.form.fields and self.form.fields[field].widget.is_hidden
            for field in self.fields
        )
        self.model_rec = model_rec
        if readonly_fields is None:
            readonly_fields = ()
        self.readonly_fields = readonly_fields

    def __iter__(self):
        for i, field in enumerate(self.fields):
            if field in self.readonly_fields:
                yield RecReadonlyField(self.form, field, is_first=(i == 0), model_rec=self.model_rec)
            else:
                yield RecField(self.form, field, is_first=(i == 0))

    def errors(self):
        return mark_safe(
            '\n'.join(
                self.form[f].errors.as_ul() for f in self.fields if f not in self.readonly_fields
            ).strip('\n')
        )


class RecField:
    def __init__(self, form, field, is_first):
        self.field = form[field]  # A django.forms.BoundField instance
        self.is_first = is_first  # Whether this field is first on the line
        self.is_checkbox = isinstance(self.field.field.widget, forms.CheckboxInput)
        self.is_readonly = False

    def label_tag(self):
        classes = []
        contents = conditional_escape(self.field.label)
        if self.is_checkbox:
            classes.append('vCheckboxLabel')

        if self.field.field.required:
            classes.append('required')
        if not self.is_first:
            classes.append('inline')
        attrs = {'class': ' '.join(classes)} if classes else {}
        # checkboxes should not have a label suffix as the checkbox appears
        # to the left of the label.
        return self.field.label_tag(
            contents=mark_safe(contents), attrs=attrs,
            label_suffix='' if self.is_checkbox else None,
        )

    def errors(self):
        return mark_safe(self.field.errors.as_ul())


class RecReadonlyField:
    def __init__(self, form, field, is_first, model_rec=None):
        # Make self.field look a little bit like a field. This means that
        # {{ field.name }} must be a useful class name to identify the field.
        # For convenience, store other field-related data here too.
        if callable(field):
            class_name = field.__name__ if field.__name__ != '<lambda>' else ''
        else:
            class_name = field

        if form._meta.labels and class_name in form._meta.labels:
            label = form._meta.labels[class_name]
        else:
            label = label_for_field(field, form._meta.model, model_rec, form=form)

        if form._meta.help_texts and class_name in form._meta.help_texts:
            help_text = form._meta.help_texts[class_name]
        else:
            help_text = help_text_for_field(class_name, form._meta.model)

        self.field = {
            'name': class_name,
            'label': label,
            'help_text': help_text,
            'field': field,
        }
        self.form = form
        self.model_rec = model_rec
        self.is_first = is_first
        self.is_checkbox = False
        self.is_readonly = True
        self.empty_value_display = model_rec.get_empty_value_display()

    def label_tag(self):
        attrs = {}
        if not self.is_first:
            attrs["class"] = "inline"
        label = self.field['label']
        return format_html('<label{}>{}:</label>', flatatt(attrs), capfirst(label))

    def contents(self):
        from rec.templatetags.rec_list import _boolean_icon
        field, obj, model_rec = self.field['field'], self.form.instance, self.model_rec
        try:
            f, attr, value = lookup_field(field, obj, model_rec)
        except (AttributeError, ValueError, ObjectDoesNotExist):
            result_repr = self.empty_value_display
        else:
            if field in self.form.fields:
                widget = self.form[field].field.widget
                # This isn't elegant but suffices for contrib.auth's
                # ReadOnlyPasswordHashWidget.
                if getattr(widget, 'read_only', False):
                    return widget.render(field, value)
            if f is None:
                if getattr(attr, 'boolean', False):
                    result_repr = _boolean_icon(value)
                else:
                    if hasattr(value, "__html__"):
                        result_repr = value
                    else:
                        result_repr = linebreaksbr(value)
            else:
                if isinstance(f.remote_field, ManyToManyRel) and value is not None:
                    result_repr = ", ".join(map(str, value.all()))
                else:
                    result_repr = display_for_field(value, f, self.empty_value_display)
                result_repr = linebreaksbr(result_repr)
        return conditional_escape(result_repr)


class InlineRecFormSet:
    """
    A wrapper around an inline formset for use in the rec system.
    """
    def __init__(self, inline, formset, fieldsets, prepopulated_fields=None,
                 readonly_fields=None, model_rec=None, has_add_permission=True,
                 has_change_permission=True, has_delete_permission=True,
                 has_view_permission=True):
        self.opts = inline
        self.formset = formset
        self.fieldsets = fieldsets
        self.model_rec = model_rec
        if readonly_fields is None:
            readonly_fields = ()
        self.readonly_fields = readonly_fields
        if prepopulated_fields is None:
            prepopulated_fields = {}
        self.prepopulated_fields = prepopulated_fields
        self.classes = ' '.join(inline.classes) if inline.classes else ''
        self.has_add_permission = has_add_permission
        self.has_change_permission = has_change_permission
        self.has_delete_permission = has_delete_permission
        self.has_view_permission = has_view_permission

    def __iter__(self):
        if self.has_change_permission:
            readonly_fields_for_editing = self.readonly_fields
        else:
            readonly_fields_for_editing = self.readonly_fields + flatten_fieldsets(self.fieldsets)

        for form, original in zip(self.formset.initial_forms, self.formset.get_queryset()):
            view_on_site_url = self.opts.get_view_on_site_url(original)
            yield InlineRecForm(
                self.formset, form, self.fieldsets, self.prepopulated_fields,
                original, readonly_fields_for_editing, model_rec=self.opts,
                view_on_site_url=view_on_site_url,
            )
        for form in self.formset.extra_forms:
            yield InlineRecForm(
                self.formset, form, self.fieldsets, self.prepopulated_fields,
                None, self.readonly_fields, model_rec=self.opts,
            )
        if self.has_add_permission:
            yield InlineRecForm(
                self.formset, self.formset.empty_form,
                self.fieldsets, self.prepopulated_fields, None,
                self.readonly_fields, model_rec=self.opts,
            )

    def fields(self):
        fk = getattr(self.formset, "fk", None)
        empty_form = self.formset.empty_form
        meta_labels = empty_form._meta.labels or {}
        meta_help_texts = empty_form._meta.help_texts or {}
        for i, field_name in enumerate(flatten_fieldsets(self.fieldsets)):
            if fk and fk.name == field_name:
                continue
            if not self.has_change_permission or field_name in self.readonly_fields:
                yield {
                    'name': field_name,
                    'label': meta_labels.get(field_name) or label_for_field(field_name, self.opts.model, self.opts),
                    'widget': {'is_hidden': False},
                    'required': False,
                    'help_text': meta_help_texts.get(field_name) or help_text_for_field(field_name, self.opts.model),
                }
            else:
                form_field = empty_form.fields[field_name]
                label = form_field.label
                if label is None:
                    label = label_for_field(field_name, self.opts.model, self.opts)
                yield {
                    'name': field_name,
                    'label': label,
                    'widget': form_field.widget,
                    'required': form_field.required,
                    'help_text': form_field.help_text,
                }

    def inline_formset_data(self):
        verbose_name = self.opts.verbose_name
        return json.dumps({
            'name': '#%s' % self.formset.prefix,
            'options': {
                'prefix': self.formset.prefix,
                'addText': gettext('Add another %(verbose_name)s') % {
                    'verbose_name': capfirst(verbose_name),
                },
                'deleteText': gettext('Remove'),
            }
        })

    @property
    def forms(self):
        return self.formset.forms

    @property
    def non_form_errors(self):
        return self.formset.non_form_errors

    @property
    def media(self):
        media = self.opts.media + self.formset.media
        for fs in self:
            media = media + fs.media
        return media


class InlineRecForm(RecForm):
    """
    A wrapper around an inline form for use in the rec system.
    """
    def __init__(self, formset, form, fieldsets, prepopulated_fields, original,
                 readonly_fields=None, model_rec=None, view_on_site_url=None):
        self.formset = formset
        self.model_rec = model_rec
        self.original = original
        self.show_url = original and view_on_site_url is not None
        self.absolute_url = view_on_site_url
        super().__init__(form, fieldsets, prepopulated_fields, readonly_fields, model_rec)

    def __iter__(self):
        for name, options in self.fieldsets:
            yield InlineFieldset(
                self.formset, self.form, name, self.readonly_fields,
                model_rec=self.model_rec, **options
            )

    def needs_explicit_pk_field(self):
        return (
            # Auto fields are editable, so check for auto or non-editable pk.
            self.form._meta.model._meta.auto_field or not self.form._meta.model._meta.pk.editable or
            # Also search any parents for an auto field. (The pk info is
            # propagated to child models so that does not need to be checked
            # in parents.)
            any(parent._meta.auto_field or not parent._meta.model._meta.pk.editable
                for parent in self.form._meta.model._meta.get_parent_list())
        )

    def pk_field(self):
        return RecField(self.form, self.formset._pk_field.name, False)

    def fk_field(self):
        fk = getattr(self.formset, "fk", None)
        if fk:
            return RecField(self.form, fk.name, False)
        else:
            return ""

    def deletion_field(self):
        from django.forms.formsets import DELETION_FIELD_NAME
        return RecField(self.form, DELETION_FIELD_NAME, False)

    def ordering_field(self):
        from django.forms.formsets import ORDERING_FIELD_NAME
        return RecField(self.form, ORDERING_FIELD_NAME, False)


class InlineFieldset(Fieldset):
    def __init__(self, formset, *args, **kwargs):
        self.formset = formset
        super().__init__(*args, **kwargs)

    def __iter__(self):
        fk = getattr(self.formset, "fk", None)
        for field in self.fields:
            if not fk or fk.name != field:
                yield Fieldline(self.form, field, self.readonly_fields, model_rec=self.model_rec)


class RecErrorList(forms.utils.ErrorList):
    """Store errors for the form/formsets in an add/change view."""
    def __init__(self, form, inline_formsets):
        super().__init__()

        if form.is_bound:
            self.extend(form.errors.values())
            for inline_formset in inline_formsets:
                self.extend(inline_formset.non_form_errors())
                for errors_in_inline_form in inline_formset.errors:
                    self.extend(errors_in_inline_form.values())
