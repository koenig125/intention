<img src="https://drive.google.com/uc?export=view&id=1qnlK7Dll-NtvVySyRckIz7255SdjZegi" width="450">

Intention is a web application that helps people make more intentional use of their time. It is built on Django web framework and interfaces with Google Calendar API to help users intelligently schedule and reschedule habits and events.

## Documentation

Visit the [wiki](https://github.com/StanfordCS194/CozyCo/wiki) for an overview of the application, record of the design process, and documentation of major modules. Addditional, technically specific documentaion is provided in module-level READMEs throughout this project.

## Local Installation:

### Getting the Code
1. Clone the [CozyCo repository](https://github.com/StanfordCS194/CozyCo.git) to your local machine.
2. Navigate to the "CocyCo/intention" directory and create a virtual environment for the applicaton.
3. With the virtual environment activated, run ```pip install -r requirements.txt``` to install project dependencies.
4. While the virtual environment is still activated, run ```manage.py makemigrations``` and ```manage.py migrate```. 

### Setting up Google Authentication and Authorization
The Intention application integrates with Google extensively. Follow the steps in the documentation to integrate [Google Application Client](https://github.com/StanfordCS194/CozyCo/wiki/Google-Application-Client), [Google Sign-In](https://github.com/StanfordCS194/CozyCo/wiki/Google-Sign-In,-Allauth,-and-User-Management), and [Google Calendar API](https://github.com/StanfordCS194/CozyCo/wiki/Google-Calendar-API) for your local version of the application.

### Run Application Locally
1. In the "CozyCo/intention" directory, run manage.py runserver 8000.
2. Navigate to http://127.0.0.1:8000/ in your browser to access the application.
