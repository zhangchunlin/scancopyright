#! /usr/bin/env python
#coding=utf-8

from uliweb.form import Form,RadioSelectField,IS_IN_SET
from uliweb.i18n import ugettext as _

SEARCH_CHOICES = [('0', '*'), ('1', 'True'),('2','False')]
class CopyrightSearchForm(Form):
    c = RadioSelectField(name='fc', id='fc', choices=SEARCH_CHOICES, validators=[IS_IN_SET(SEARCH_CHOICES)], default='0', label = _('Having Copyright'),html_attrs={'_class':'radio inline'},)
    ci = RadioSelectField(name='fci', id='fci', choices=SEARCH_CHOICES, validators=[IS_IN_SET(SEARCH_CHOICES)], default='0', label = _('Copyright Inhouse'),html_attrs={'_class':'radio inline'},)
    cg = RadioSelectField(name='fcg', id='fcg', choices=SEARCH_CHOICES, validators=[IS_IN_SET(SEARCH_CHOICES)], default='0', label = _('Copyright GPL'),html_attrs={'_class':'radio inline'},)
    co = RadioSelectField(name='fco', id='fco', choices=SEARCH_CHOICES, validators=[IS_IN_SET(SEARCH_CHOICES)], default='0', label = _('Copyright Other Opensource'),html_attrs={'_class':'radio inline'},)
