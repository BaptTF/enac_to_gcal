from __future__ import print_function

import logging
import time
import string
import re
import sys
import os
import shutil
import fileinput

import googleapiclient
import arrow
from googleapiclient import errors
from icalevents.icalevents import events
from dateutil.tz import gettz

from datetime import datetime, timezone, timedelta

from auth import auth_with_calendar_api
from pathlib import Path
from httplib2 import Http

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.alert import Alert

config = {}
config_path=os.environ.get('CONFIG_PATH', 'config.py')
exec(Path(config_path).read_text(), config)

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
if config.get('LOGFILE', None):
    handler = logging.FileHandler(filename=config['LOGFILE'], mode='a')
else:
    handler = logging.StreamHandler(sys.stderr)
handler.setFormatter(logging.Formatter('%(asctime)s|[%(levelname)s] %(message)s'))
logger.addHandler(handler)

DEFAULT_TIMEDELTA = timedelta(days=365)


def get_enac_ics(downloadPath, icsPath, url, user, password, nombre_de_mois):

    #nous devrions vérifier si le fichier existe ou non avant de le supprimer.
    logger.info(f"> Processing: {nombre_de_mois} month")
    if os.path.exists(icsPath + "/planning.ics"):
        logger.info("Suppression du fichier: " + icsPath + "/planning.ics")
        os.remove(icsPath + "/planning.ics")
    else:
        logger.error("Impossible de supprimer le fichier planning.ics car il n'existe pas")
    for i in range(1,nombre_de_mois):
        if os.path.exists(icsPath + f"/planning ({i}).ics"):
            os.remove(icsPath + f"/planning ({i}).ics")
        else:
            logger.error(f"Impossible de supprimer le fichier planning ({i}).ics car il n'existe pas")
            print(f"Impossible de supprimer le fichier planning ({i}).ics car il n'existe pas")
    chrome_options = Options()
    chrome_options.add_argument('--headless=new')  # Run browser in headless mode
    #browser_locale = 'fr'
    #chrome_options.add_argument("--lang={}".format(browser_locale))
    logger.info("> Lancement du navigateur")
    driver = webdriver.Chrome(options=chrome_options)
    driver.implicitly_wait(10)
    logger.info("> Connexion au site de ENAC")
    driver.get(url)
    if driver.find_element(By.ID, "j_idt30:j_idt40_label").text != "Français":
        driver.find_element(By.XPATH, "//div[@class='ui-selectonemenu-trigger ui-state-default ui-corner-right']").click()
        time.sleep(2)
        driver.find_element(By.ID, "j_idt30:j_idt40_1").click()
        time.sleep(2)
        alert = Alert(driver)
        alert.accept()
        time.sleep(2)
    driver.find_element(By.ID, "username").send_keys(user)
    driver.find_element(By.ID, "password").send_keys(password)
    logger.info("> Login Success")
    time.sleep(2)
    driver.find_element(By.ID, "j_idt28").click()
    time.sleep(2)
    try:
        driver.find_element(By.LINK_TEXT, "Mon emploi du temps").click()
    except:
        driver.find_element(By.LINK_TEXT, "My schedule").click()
    time.sleep(2)
    driver.find_element(By.XPATH, "//button[@class='fc-month-button ui-button ui-state-default ui-corner-left ui-corner-right']").click()
    time.sleep(2)
    logger.info("Téléchargement du planning pour le mois: " + str(1))
    driver.find_element(By.ID, "form:j_idt121").click()
    time.sleep(2)
    for _ in range(2,nombre_de_mois+1):
        try:
            logger.info("Téléchargement du planning pour le mois: " + str(_))
            driver.find_element(By.XPATH, '//body').send_keys(Keys.CONTROL + Keys.HOME)
            time.sleep(5)
            driver.find_element(By.XPATH, "//button[@class='fc-next-button ui-button ui-state-default ui-corner-left ui-corner-right']").click()
            time.sleep(5)
            driver.find_element(By.ID, "form:j_idt121").click()
            time.sleep(5)
        except:
            logger.error("Erreur lors du téléchargement du planning pour le mois: " + str(_))
    time.sleep(2)

    #cut paste the ics file
    if os.path.exists(downloadPath + "/planning.ics"):
        logger.info("> Moving downloaded ics")
        shutil.move(downloadPath + "/planning.ics", icsPath)
    else:
        logger.error("Impossible de déplacer le fichier planning.ics car il n'existe pas")
    for i in range(1,nombre_de_mois):
        if os.path.exists(downloadPath + f"/planning ({i}).ics"):
            shutil.move(downloadPath + f"/planning ({i}).ics", icsPath)
        else:
            logger.error(f"Impossible de déplacer le fichier planning ({i}).ics car il n'existe pas")
    time.sleep(2)

def patch_ics_files(directory):
    """
    Patch all .ics files in the specified directory by replacing the X-WR-TIMEZONE property
    with a standard timezone definition.
    """
    # Specify the replacement value for X-WR-TIMEZONE
    replacement = """BEGIN:VTIMEZONE
TZID:Europe/Paris
BEGIN:STANDARD
DTSTART:19710101T030000
TZOFFSETFROM:+0200
TZOFFSETTO:+0100
END:STANDARD
END:VTIMEZONE"""

    # Loop over each file in the directory
    for filename in os.listdir(directory):
        # Check that the file has a .ics extension
        if filename.endswith('.ics'):
            # Open the file for in-place editing
            with fileinput.FileInput(os.path.join(directory, filename), inplace=True) as file:
                # Loop over each line in the file
                for line in file:
                    # Replace the X-WR-TIMEZONE property with the replacement value
                    if line.startswith('X-WR-TIMEZONE:'):
                        print(replacement)
                    else:
                        print(line, end='')

def get_current_events_from_files(path):
    
    """Retrieves data from iCal files.  Assumes that the files are all
    *.ics files located in a single directory.

    Returns the parsed list of events or None if an error occurs.
    """

    from glob import glob
    from os.path import join

    event_ics = glob(join(path, '*.ics'))

    logger.debug('> Found {} local .ics files in {}'.format(len(event_ics), join(path, '*.ics')))
    if len(event_ics) > 0:
        ics = event_ics[0]
        logger.debug('> Loading file {}'.format(ics))
        cal = get_current_events(feed_url_or_path=ics, files=True)
        logger.debug('> Found {} new events'.format(len(cal)))
        for ics in event_ics[1:]:
            logger.debug('> Loading file {}'.format(ics))
            evt = get_current_events(feed_url_or_path=ics, files=True)
            if len(evt) > 0:
                cal.extend(evt)
            logger.debug('> Found {} new events'.format(len(evt)))
        return cal
    else:
        return None

def get_current_events(feed_url_or_path, files):
    """Retrieves data from an iCal feed and returns a list of icalevents
    Event objects

    Returns the parsed list of events or None if an error occurs.
    """

    events_end = datetime.now()
    if config.get('ICAL_DAYS_TO_SYNC', 0) == 0:
        # default to 1 year ahead
        events_end += DEFAULT_TIMEDELTA
    else:
        # add on a number of days
        events_end += timedelta(days=config['ICAL_DAYS_TO_SYNC'])

    try:
        if files:
            cal = events(file=feed_url_or_path, end=events_end)
        else:
            # directly configure http connection object to set ssl and authentication parameters
            http_conn = Http(disable_ssl_certificate_validation=not config.get('ICAL_FEED_VERIFY_SSL_CERT', True))

            if config.get('ICAL_FEED_USER') and config.get('ICAL_FEED_PASS'):
                # credentials used for every connection
                http_conn.add_credentials(name=config.get('ICAL_FEED_USER'), password=config.get('ICAL_FEED_PASS'))

            cal = events(feed_url_or_path, start=datetime.now()-timedelta(days=config.get('PAST_DAYS_TO_SYNC', 0)), end=events_end, http=http_conn)
    except Exception as e:
        logger.error('> Error retrieving iCal data ({})'.format(e))
        return None

    return cal

def get_gcal_events(calendar_id, service, from_time=None):
    """Retrieves the current set of Google Calendar events from the selected
    user calendar. If from_time is not specified, includes events from all-time.

    Returns a dict containing the event(s) existing in the calendar.
    """

    # The list() method returns a dict containing various metadata along with the actual calendar entries (if any). 
    # It is not guaranteed to return all available events in a single call, and so may need called multiple times
    # until it indicates no more events are available, signalled by the absence of "nextPageToken" in the result dict

    logger.debug('Retrieving Google Calendar events')

    # make an initial call, if this returns all events we don't need to do anything else,,,
    events_result = service.events().list(calendarId=calendar_id,
                                         timeMin=from_time, 
                                         singleEvents=True, 
                                         orderBy='startTime', 
                                         showDeleted=True).execute()

    events = events_result.get('items', [])
    # if nextPageToken is NOT in the dict, this should be everything
    if 'nextPageToken' not in events_result:
        logger.info('> Found {:d} upcoming events in Google Calendar (single page)'.format(len(events)))
        return events

    # otherwise keep calling the method, passing back the nextPageToken each time
    while 'nextPageToken' in events_result:
        token = events_result['nextPageToken']
        events_result = service.events().list(calendarId=calendar_id,
                                             timeMin=from_time, 
                                             pageToken=token, 
                                             singleEvents=True, 
                                             orderBy='startTime', 
                                             showDeleted=True).execute()
        newevents = events_result.get('items', [])
        events.extend(newevents)
        logger.debug('> Found {:d} events on new page, {:d} total'.format(len(newevents), len(events)))
    
    logger.info('> Found {:d} upcoming events in Google Calendar (multi page)'.format(len(events)))
    return events

def get_gcal_datetime(py_datetime, gcal_timezone):
    py_datetime = py_datetime.astimezone(gettz(gcal_timezone))
    return {u'dateTime': py_datetime.strftime('%Y-%m-%dT%H:%M:%S%z'), 'timeZone': gcal_timezone}

def get_gcal_date(py_datetime):
    return {u'date': py_datetime.strftime('%Y-%m-%d')}

def create_id(uid, begintime, endtime, prefix=''):
    """ Converts ical UUID, begin and endtime to a valid Gcal ID

    Characters allowed in the ID are those used in base32hex encoding, i.e. lowercase letters a-v and digits 0-9, see section 3.1.2 in RFC2938
    Te length of the ID must be between 5 and 1024 characters
    https://developers.google.com/resources/api-libraries/documentation/calendar/v3/python/latest/calendar_v3.events.html

    Returns:
        ID
    """
    allowed_chars = string.ascii_lowercase[:22] + string.digits
    return prefix + re.sub('[^{}]'.format(allowed_chars), '', uid.lower()) + str(arrow.get(begintime).int_timestamp) + str(arrow.get(endtime).int_timestamp)

if __name__ == '__main__':
    mandatory_configs = ['CREDENTIAL_PATH', 'ICAL_FEEDS', 'APPLICATION_NAME']
    for mandatory in mandatory_configs:
        if not config.get(mandatory) or config[mandatory][0] == '<':
            logger.error("Must specify a non-blank value for %s in the config file" % mandatory)
            sys.exit(1)

    # setting up Google Calendar API for use
    logger.debug('> Loading credentials')
    service = auth_with_calendar_api(config)

    # dateime instance representing the start of the current day (UTC)
    today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)

    for feed in config.get('ICAL_FEEDS'):
        logger.info('> Processing source %s' % feed['source'])

        # retrieve events from Google Calendar, starting from beginning of current day
        logger.info('> Retrieving events from Google Calendar')
        gcal_events = get_gcal_events(calendar_id=feed['destination'], service=service, from_time=(today-timedelta(days=config.get('PAST_DAYS_TO_SYNC', 0))).isoformat())

        # retrieve events from the iCal feed
        if feed['files']:
            logger.info('> Downloading events from ENAC')
            get_enac_ics(feed['download'],feed['source'],'https://aurion-prod.enac.fr/faces/Login.xhtml',config.get('ICAL_FEED_USER'),config.get('ICAL_FEED_PASS'),config.get('ICAL_DAYS_TO_SYNC') // 30)
            logger.info('> Patching iCal files for google timezone')
            patch_ics_files(feed['source'])
            logger.info('> Retrieving events from local folder')
            ical_cal = get_current_events_from_files(feed['source'])
        else:
            logger.info('> Retrieving events from iCal feed')
            ical_cal = get_current_events(feed_url_or_path=feed['source'], files=False)

        if ical_cal is None:
            sys.exit(-1)

        # convert iCal event list into a dict indexed by (converted) iCal UID
        ical_events = {}

        for ev in ical_cal:
            # explicitly set any events with no timezone to use UTC (icalevents
            # doesn't seem to do this automatically like ics.py)
            if ev.start.tzinfo is None:
                ev.start = ev.start.replace(tzinfo=timezone.utc)
            if ev.end is not None and ev.end.tzinfo is None:
                ev.end = ev.end.replace(tzinfo=timezone.utc)

            try:
                if 'EVENT_PREPROCESSOR' in config:
                    keep = config['EVENT_PREPROCESSOR'](ev)
                    if not keep:
                        logger.debug("Skipping event %s - EVENT_PREPROCESSOR returned false" % (str(ev)))
                        continue

            except Exception as ex:
                logger.error("Error processing entry (%s, %s) - leaving as-is" % (str(ev), str(ex)))

            ical_events[create_id(ev.uid, ev.start, ev.end, config.get('EVENT_ID_PREFIX', ''))] = ev

        logger.debug('> Collected {:d} iCal events'.format(len(ical_events)))

        # retrieve the Google Calendar object itself
        gcal_cal = service.calendars().get(calendarId=feed['destination']).execute()
        logger.info('> Processing Google Calendar events...')
        gcal_event_ids = [ev['id'] for ev in gcal_events]

        # first check the set of Google Calendar events against the list of iCal
        # events. Any events in Google Calendar that are no longer in iCal feed
        # get deleted. Any events still present but with changed start/end times
        # get updated.
        for gcal_event in gcal_events:
            eid = gcal_event['id']

            if eid not in ical_events:
                # if a gcal event has been deleted from iCal, also delete it from gcal.
                # Apparently calling delete() only marks an event as "deleted" but doesn't
                # remove it from the calendar, so it will continue to stick around.
                # If you keep seeing messages about events being deleted here, you can
                # try going to the Google Calendar site, opening the options menu for
                # your calendar, selecting "View bin" and then clicking "Empty bin
                # now" to completely delete these events.
                try:
                    # already marked as deleted, so it's in the "trash" or "bin"
                    if gcal_event['status'] == 'cancelled': continue

                    logger.info(u'> Deleting event "{}" from Google Calendar...'.format(gcal_event.get('summary', '<unnamed event>')))
                    service.events().delete(calendarId=feed['destination'], eventId=eid).execute()
                    time.sleep(config['API_SLEEP_TIME'])
                except googleapiclient.errors.HttpError:
                    pass # event already marked as deleted
            else:
                ical_event = ical_events[eid]
                gcal_begin = arrow.get(gcal_event['start'].get('dateTime', gcal_event['start'].get('date')))
                gcal_end = arrow.get(gcal_event['end'].get('dateTime', gcal_event['end'].get('date')))

                gcal_has_location = bool(gcal_event.get('location'))
                ical_has_location = bool(ical_event.location)

                gcal_has_description = 'description' in gcal_event
                ical_has_description = ical_event.description is not None

                # event name can be left unset, in which case there's no summary field
                gcal_name = gcal_event.get('summary', None)
                log_name = '<unnamed event>' if gcal_name is None else gcal_name
                #logger.debug(f"time_differ = {gcal_begin}, {ical_event.start}, {gcal_end}, {ical_event.end}")
                times_differ = gcal_begin != ical_event.start or gcal_end != ical_event.end
                titles_differ = gcal_name != ical_event.summary
                locs_differ = gcal_has_location != ical_has_location and gcal_event.get('location') != ical_event.location
                descs_differ = gcal_has_description != ical_has_description and (gcal_event.get('description') != ical_event.description)

                needs_undelete = config.get('RESTORE_DELETED_EVENTS', False) and gcal_event['status'] == 'cancelled'

                changes = []
                if times_differ: changes.append("start/end times")
                if titles_differ: changes.append("titles")
                if locs_differ: changes.append("locations")
                if descs_differ: changes.append("descriptions")
                if needs_undelete: changes.append("undeleted")

                # check if the iCal event has a different: start/end time, name, location,
                # or description, and if so sync the changes to the GCal event
                if needs_undelete or times_differ or titles_differ or locs_differ or descs_differ:
                    logger.info(u'> Updating event "{}" due to changes: {}'.format(log_name, ", ".join(changes)))
                    delta = ical_event.end - ical_event.start
                    # all-day events handled slightly differently
                    # TODO multi-day events?
                    if delta.days >= 1:
                        gcal_event['start'] = get_gcal_date(ical_event.start)
                        gcal_event['end'] = get_gcal_date(ical_event.end)
                    else:
                        gcal_event['start'] = get_gcal_datetime(ical_event.start, gcal_cal['timeZone'])
                        if ical_event.end is not None:
                            gcal_event['end']   = get_gcal_datetime(ical_event.end, gcal_cal['timeZone'])

                    # if the event was deleted, the status will be 'cancelled' - this restores it
                    gcal_event['status'] = 'confirmed'

                    gcal_event['summary'] = ical_event.summary
                    gcal_event['description'] = ical_event.description
                    if feed['files']:
                        url_feed = 'https://events.from.ics.files.com'
                    else:
                        url_feed = feed['source']
                    gcal_event['source'] = {'title': 'Imported from ical_to_gcal_sync.py', 'url': url_feed}
                    gcal_event['location'] = ical_event.location

                    service.events().update(calendarId=feed['destination'], eventId=eid, body=gcal_event).execute()
                    time.sleep(config['API_SLEEP_TIME'])

        # now add any iCal events not already in the Google Calendar
        logger.info('> Processing iCal events...')
        for ical_id, ical_event in ical_events.items():
            if ical_id not in gcal_event_ids:
                gcal_event = {}
                gcal_event['summary'] = ical_event.summary
                gcal_event['id'] = ical_id
                gcal_event['description'] = ical_event.description
                if feed['files']:
                    url_feed = 'https://events.from.ics.files.com'
                else:
                    url_feed = feed['source']
                gcal_event['source'] = {'title': 'Imported from ical_to_gcal_sync.py', 'url': url_feed}
                gcal_event['location'] = ical_event.location

                # check if no time specified in iCal, treat as all day event if so
                delta = ical_event.end - ical_event.start
                # TODO multi-day events?
                if delta.days >= 1:
                    gcal_event['start'] = get_gcal_date(ical_event.start)
                    logger.info(u'iCal all-day event {} to be added at {}'.format(ical_event.summary, ical_event.start))
                    if ical_event.end is not None:
                        gcal_event['end'] = get_gcal_date(ical_event.end)
                else:
                    gcal_event['start'] = get_gcal_datetime(ical_event.start, gcal_cal['timeZone'])
                    logger.info(u'iCal event {} to be added at {}'.format(ical_event.summary, ical_event.start))
                    if ical_event.end is not None:
                        gcal_event['end'] = get_gcal_datetime(ical_event.end, gcal_cal['timeZone'])

                logger.info('Adding iCal event called "{}", starting {}'.format(ical_event.summary, gcal_event['start']))

                try:
                    time.sleep(config['API_SLEEP_TIME'])
                    service.events().insert(calendarId=feed['destination'], body=gcal_event).execute()
                except Exception as ei:
                    logger.warning("Error inserting: %s (%s)" % (gcal_event['id'], str(ei)))
                    time.sleep(config['API_SLEEP_TIME'])
                    try:
                        service.events().update(calendarId=feed['destination'], eventId=gcal_event['id'], body=gcal_event).execute()
                    except Exception as ex:
                        logger.error("Error updating: %s (%s)" % (gcal_event['id'], ex))

        logger.info('> Processing of source %s completed' % feed['source'])
