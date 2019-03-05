Intention is a web application that helps people make more intentional use of their time. It is built on Django web framework and interfaces with Google Calendar API to help users intelligently schedule and reschedule tasks, projects, and habits.

## Features:

- Intelligently reschedule events and tasks based on preferences and deadlines.
- Auto-schedule large chunks of time for projects with a deadline.
- Auto-schedule small chunks of time for miscellaneous tasks.
- Auto-schedule recurring events to achieve habits or goals.

## Local Installation and Deployment:

### Getting the Code
1. Clone the [CozyCo repository](https://github.com/StanfordCS194/CozyCo.git) to your local machine.
2. Navigate to the "CocyCo/intention" directory and create a virtual environment for the applicaton.
3. With the virtual environment activated, run ```pip install -r requirements.txt``` to install project dependencies.
4. While the virtual environment is still activated, run ```manage.py makemigrations``` and ```manage.py migrate```. 

### Create a Google Project
Any application that calls Google APIs needs to set up a Google project appropriately. 
1. Decide which google account will own the project that makes API calls on behalf of the application. You can use an existing account or create a new account explicitly dedicated to API calls for the Intention application.
2. Log into the [Google API Console Dashboard](https://console.developers.google.com/apis/dashboard?project=intention-webapp) with your chosen account.
3. Create a new project for the application.

### Enable Google Calendar API
1. Open the [Library](https://console.developers.google.com/apis/library?refresh=1) page in the API Console.
2. Select the project associated with your application, created in the previous section.
3. Use the Library page to search for "Google Calendar API". Click on the API, then click "Enable".

### Create Authorization Credentials
1. Open the [Credentials](https://console.developers.google.com/apis/credentials?refresh=1) page in the API Console.
2. Click "Create credentials > OAuth client ID".
3. You will be prompted to set a product name on the consent screen. Upon clicking "Configure consent screen", give a name for the client. This is the name that will be displayed to the user during authorization.
4. On the same page, click on "Add scope", then check the checkbox for "../auth/calendar". Click "Add". Then, click "save" at the bottom of the page to return to the client ID page.
3. Set the application type to "Other". Give a name for the application client. In contrast to the name set in step 3, this name will remain private and will only be visible to you on your API Console. Click "Create" once finished.
4. Once the creation process has completed, download the "client_secret.json" file from the Credentials page.
5. Rename the downloaded file "credentials.json" and add it to the "CozyCo/intention" directory.

### Run Application Locally
1. In the "CozyCo/intention" directory, run manage.py runserver 8000.
2. Navigate to http://127.0.0.1:8000/ in your browser to access the application.