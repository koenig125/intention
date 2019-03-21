Settings.py and urls.py are the primary files through which the django-allauth package is integrated into the application. A brief overview of django-allauth, its function in the application, motivation for choosing it as the 3rd-party login provider, and its approach to user creation and account management can be found in the wiki [here](https://github.com/StanfordCS194/CozyCo/wiki/Google-Sign-In,-Allauth,-and-User-Management). 

### Settings
Settings of note for django-allauth:
1. SITE_ID - The id of the site domain in the django admin page from which django-allauth expects login requests. The setup process specified in the [documentation](https://github.com/StanfordCS194/CozyCo/wiki/Google-Sign-In,-Allauth,-and-User-Management) ensures the site id for the development domain 127.0.0.1 is 1. However, if you wish to run the application on an alternative local domain (ie localhost, etc.) or deploy the application remotely, you must add another site domain in the django admin page and change the SITE_ID field to match the id of the new domain (the second site domain added would have id 2, the third 3, and so on).
2. INSTALLED_APPS - The 'allauth.socialaccount.providers.google' line in INSTALLED_APPS enables Google as a login provider. To add new providers, you need to add an additional line for each new provider in this setting.
3. OAUTHLIB_INSECURE_TRANSPORT - Allows login to take place over insecure (ie http instead of https) connections. This setting is required for local development, but should be disabled upon deployment.

### URLS
path('accounts/', include('allauth.urls')) includes the django-allauth url patterns, which override the native django login and logout pages to facilitate third party login.
