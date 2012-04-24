#! /usr/bin/env python
#coding=utf-8

from uliweb.form import Form,RadioSelectField,IS_IN_SET,Submit,BooleanField,TextField
from uliweb.i18n import ugettext as _

class CrconflictForm(Form):
    form_buttons = Submit(value='查询版权冲突的所有文件')


SEARCH_CHOICES = [('0', '*'), ('1', 'True'),('2','False')]
class CopyrightSearchForm(Form):
    form_buttons = Submit(value='按版权扫描结果搜索文件列表')
    c = RadioSelectField(name='fc', id='fc', choices=SEARCH_CHOICES, validators=[IS_IN_SET(SEARCH_CHOICES)], default='0', label = _('Having Copyright'),html_attrs={'_class':'radio inline'},)
    ci = RadioSelectField(name='fci', id='fci', choices=SEARCH_CHOICES, validators=[IS_IN_SET(SEARCH_CHOICES)], default='0', label = _('Copyright Inhouse'),html_attrs={'_class':'radio inline'},)
    cg = RadioSelectField(name='fcg', id='fcg', choices=SEARCH_CHOICES, validators=[IS_IN_SET(SEARCH_CHOICES)], default='0', label = _('Copyright GPL'),html_attrs={'_class':'radio inline'},)
    co = RadioSelectField(name='fco', id='fco', choices=SEARCH_CHOICES, validators=[IS_IN_SET(SEARCH_CHOICES)], default='0', label = _('Copyright Other Opensource'),html_attrs={'_class':'radio inline'},)

class ReleaseForm(Form):
    release = BooleanField(name='release_bool',id='release_bool',label = _('Release this package'))
    rnote = TextField(label =_('release note'), name='rnote', id='rnote', rows="6")
