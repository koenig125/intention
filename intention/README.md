<img src="https://drive.google.com/uc?export=view&id=14V68cgr_oBSuu4gtro6cupeGe_dg42rz" width="450">

Intention is a web application that helps people use time intentionally. It is built on Django web framework and interfaces with Google Calendar API to enable users to intelligently schedule and reschedule habits and events.

## Documentation

The [wiki](https://github.com/StanfordCS194/CozyCo/wiki) contains the bulk of the project documentation. Specifically, it addresses:
* Major application modules and motivation for their development.
* Frontend development, including application design and user interface.
* Project process, including benchmarking, need finding, and user testing.

In addition, technically specific documentaion is provided in module-level READMEs throughout this project.
* The [intention](https://github.com/StanfordCS194/CozyCo/tree/documentation/intention/intention) README details integration with django-allauth.
* The [intention_app](https://github.com/StanfordCS194/CozyCo/tree/documentation/intention/intention_app) README details application views, forms, and models.
* The [scheduling](https://github.com/StanfordCS194/CozyCo/tree/documentation/intention/intention_app/scheduling) README details scheduler and rescheduler implementations.

## Local Installation:

### Getting the Code
1. Clone the [CozyCo repository](https://github.com/StanfordCS194/CozyCo.git) to your local machine.
2. Navigate to the "CocyCo/intention" directory and create a virtual environment for the applicaton.
3. With the virtual environment activated, run ```pip install -r requirements.txt``` to install project dependencies.
4. While the virtual environment is still activated, run ```manage.py makemigrations``` and ```manage.py migrate```. 

### Setting up Google Authentication and Authorization
Intention integrates with Google extensively. Follow the steps in the wiki to do the following:
1. Create a [Google Application Client](https://github.com/StanfordCS194/CozyCo/wiki/Google-Application-Client).
2. Enable [Google Sign-In](https://github.com/StanfordCS194/CozyCo/wiki/Google-Sign-In,-Allauth,-and-User-Management) with django-allauth.
3. Enable [Google Calendar API](https://github.com/StanfordCS194/CozyCo/wiki/Google-Calendar-API) requests.

### Running the Application
1. In the "CozyCo/intention" directory, run manage.py runserver 8000.
2. Navigate to http://127.0.0.1:8000/ in your browser to access the application.
