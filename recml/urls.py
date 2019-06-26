# -*- coding: utf-8 -*-

"""
@Time        : 2019/6/2 9:15 PM
@Author      : Patrick Yang
@Email       : 490286710@qq.com
@File        : urls.py
@Software    : PyCharm
"""

from django.urls import path

from . import views

app_name = 'recml'
urlpatterns = [
    path('', views.IndexView.as_view(), name='index')
]