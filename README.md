## IMPORTANT
> NOTE: requires Python 3.7+

Ce script utilise **Google Chrome** principalement parce que c'est le navigateur le plus utilisé, si tu veux utilisé un autre navigateur tu peux modifier `ical_to_gcal_sync.py` ligne 61-66

## UTILISER LE SCRIPT

1. Copy `config.py.example` to a new file `config.py` or a custom file (see *Multiple Configurations* below)
2. Modify the value of `ICAL_FEEDS` to configure your calendars. It should contain a list with one or more entries where each entry is a dict with the following structure:
```python
ICAL_FEEDS = [
    {
        # the ID of the Google calendar to insert events into. this can be "primary" if you want to use the
        # default main calendar, or a 'longID@group.calendar.google.com' string for secondary calendars. You
        # can find the long calendar ID on its settings page.
        'destination': '<GOOGLE CAL ID>',
        # put your path of your download file
        "download": r"<Path to your download folder>"
    },
]
```
3. Tu dois mettre ton nom d'utilisateur et mdp dans `ICAL_FEED_USER` et `ICAL_FEED_PASS`. 
4. Run `pip install -r requirements.txt`
5. Go through the process of registering an app in the Google Calendar API dashboard in order to obtain an OAuth client ID. This process is described at https://developers.google.com/google-apps/calendar/quickstart/python. It's important to select "Desktop app" for the OAuth "Application Type" field. Once the credentials are created, download the JSON file, rename it to `ical_to_gcal_sync_client_secret.json` and  place it in the same location as the script. 
6. Until recently you could leave your Google Cloud project in "testing" mode and the OAuth flow would work indefinitely. However as [described here](https://support.google.com/cloud/answer/10311615#publishing-status&zippy=%2Ctesting) any tokens for apps in this mode will now expire after 7 days, including refresh tokens. To avoid having to manually re-auth every time this happens, go to [your OAuth consent page configuration](https://console.cloud.google.com/apis/credentials/consent) and set the "Publishing status" to "Production". This will display a warning that you need to do a lot of verification steps, but things still seem to work if you ignore the warnings. 
7. Run the script. This should trigger the OAuth2 authentication process and prompt you to allow the app you created in step 5 to access your calendars. If successful it should store the credentials in `ical_to_gcal_sync_credentials.json`.
8. Subsequent runs of the script should not require any further interaction unless the credentials are invalidated/changed.

## OAuth workarounds

If you're running the script on a headless device you may have some issues with step 7 above. It normally attempts to auto-open a browser to allow you to authorise the request, and will print a URL to visit instead if it can't find a browser/display. You can visit this URL from another device, but the final step in the auth flow is an HTTP request sent back to the server started by `auth.py`. This will fail when you're using another device because the URL it redirects your browser to will be `http://localhost:port/...`. To workaround this there are a few options:
 - clone the repo to another machine, run the auth flow there, and then copy the saved credentials file to the headless device
 - copy the `http://localhost:port/...` URL and then in an SSH session on the headless device run `curl <URL>` 
 - alternatively if your headless device has open ports, you can modify the `run_local_server()` line in auth.py to have the Google redirect point to a hostname other than `localhost`. See the `host` and `port` parameters in the [documentation](https://google-auth-oauthlib.readthedocs.io/en/latest/reference/google_auth_oauthlib.flow.html#google_auth_oauthlib.flow.InstalledAppFlow.run_local_server) 

## Multiple Configurations / Alternate Config Location

If you want to specify an alternate location for the config.py file, use the environment variable CONFIG_PATH:

```bash
CONFIG_PATH='/path/to/my-custom-config.py' python ical_to_gcal_sync.py
```

## Rewriting Events / Skipping Events

If you specify a function in the config file called EVENT_PREPROESSOR, you can use that
function to rewrite or even skip events from being synced to the Google Calendar.

Some example rewrite rules:

```python
import icalevents
def EVENT_PREPROCESSOR(ev: icalevents.icalparser.Event) -> bool:
    from datetime import timedelta

    # Skip Bob's out of office messages
    if ev.summary == "Bob OOO":
        return False

    # Skip gaming events when we're playing Monopoly
    if ev.summary == "Gaming" and "Monopoly" in ev.description:
        return False

    # convert fire drill events to all-day events
    if ev.summary == "Fire Drill":
        ev.all_day = True
        ev.start = ev.start.replace(hour=0, minute=0, second=0)
        ev.end = ev.start + timedelta(days=1)

    # include all other entries
    return True
```
