"""intention URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from intention_app.views import homepage_view, schedule_view, reschedule_view, calendar_view
from django.conf.urls import url

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', homepage_view, name='homepage'),
    path('schedule', schedule_view, name='schedule_view'),
    path('reschedule', reschedule_view, name='reschedule_view'),
    path('calendar', calendar_view, name='calendar_view'),
    url(r'', homepage_view, name="homepage"),
]