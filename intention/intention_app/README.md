## Application Overview

Intention operates with a traditional web application infrastructure powered by Django. There are four files of note:

- **urls** specifies the addresses to each of the application's pages.
- **views** coordinates the interaction between each web page and the user.
- **forms** details the Django forms for task, project, and habit scheduling.
- **models** defines schemas for user preference information stored in the database.

The **scheduling** module contains the back-end logic for scheduling and rescheduling requests. This module has 3 main responsibilities:

1. Communicating with the database to retrieve user preferences.
2. Interfacing with Google Calendar API to access and add to user calendars.
3. Intelligently scheduling new events and tasks according to user constraints.

Details of these responsibilities and implementation documentation is provided in the module's readme. 

Outside of the scheduling module, the application also communicates with Google Oauth during the login process. Users are required to login with their Google account when they first access the site in order to facilitate scheduling functionality and persistence of user preferences. 

## Application Architecture

The components of the application described above come together as represented in the architecture diagram below:

<img src="https://github.com/StanfordCS194/Team-5/blob/master/team-photos/architecture-diagram.jpg" width="800">

We have sketched out the front end flow and design on figma. You can check out our prototype here: https://www.figma.com/file/d5jsjBeO4UWY6lmy3op35G2S/CozyCo?node-id=0%3A1
