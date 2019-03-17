The views, forms, and models files are the foundation of the application. There are two significant components of the application that are particularly concentrated in these files: Google OAuth 2.0 authorization and user preferences.

### Google Authorization

As detailed in the Google Calendar API [wiki page](https://github.com/StanfordCS194/CozyCo/wiki/Google-Calendar-API), Intention follows standard OAuth 2.0 protocol to access user Google Calendar resources. This protocol is initiated in the **authorize** function in views.py if the user tries is routed to any view that leads to a page that requires access to a user's Google Calendar. Because the authorization process could be initiated from several different views, the initating view stores its url path in the session as **endurl**. This path is then accessed by the **oauth2callback** function, which is called to handle the response after the user confirms or denies access to their Google Calendar. If authorization is successful, the oauth2callback function reroutes the user to the initiator path stored in the session. A refresh token is requested in the authorization process and stored along with the authorization credentials upon success. The refresh token enables the application to renew expired access tokens so that the user only has to authorize the application once post-login. For additional details about access tokens, refresh tokens, and the OAuth 2.0 process, see the [official documentation](https://developers.google.com/identity/protocols/OAuth2).

### User Preferences

The application requests user preferences to better guide scheduling decisions. These preferences are persisted in Django's built-in SQLite database. There are four preference fields as defined in the Preferences class in models.py:

1. Wake time - Time at which user typically wakes.
2. Sleep time - TIme at which user typically sleeps.
3. Main Calendar - Calendar to which events will be added when scheduled or rescheduled.
4. Calendar list - List of calendars from which to take events into account when scheduling.

Users input the information for these fields through the TimeForm, MainCalForm, and AllCalsForm forms specified in forms.py. If a user does not specify a main calendar, the primary calendar for their google account is utilized for both their main calendar and calendar list. See the user testing [wiki page](https://github.com/StanfordCS194/CozyCo/wiki/User-Testing) for details on user preferences motivation.
