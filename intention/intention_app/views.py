from django.shortcuts import render
from django.http import HttpResponse


# A Sample View to Render CozyCo Logo 
def logo_view(request):
    image_data = open("intention_app/static/cozyco-logo.png", "rb").read()  
    return HttpResponse(image_data, content_type="image/png")