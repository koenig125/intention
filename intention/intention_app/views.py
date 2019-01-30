from django.shortcuts import render
from django.http import HttpResponse
from django.template import loader

# A Sample View to Render CozyCo Logo 
def logo_view(request):
    image_data = open("intention_app/static/cozyco-logo.png", "rb").read()
    return HttpResponse(image_data, content_type="image/png")

# Renders the Intention App homepage
def homepage_view(request):
    template = loader.get_template('home.html')
    context = {
        'message': 'Let\'s get productive!',
    }
    return HttpResponse(template.render(context, request))