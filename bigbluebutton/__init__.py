# Copyright: 2011 Steve Challis (http://schallis.com)
# Copyright: 2012 MoinMoin:ReimarBauer
# License: MIT 

"""
    bigbluebutton

    

    This module contains functions to access bigbluebutton servers
    Meeting_Setup: for initializing a meeting.
    Meeting: for operations on the meeting after initializing.
    
"""
from urllib2 import urlopen
from urllib import urlencode
from hashlib import sha1
import xml.etree.ElementTree as ET
import random
from bigbluebutton.utils import api_call, get_xml


class Meeting_Setup(object):
    """
    Initializes meetings
    """
    def __init__(self, bbb_api_url=None, salt=None, meeting_name='', meeting_id='', attendee_password=None, moderator_password=None):
        """
        :param bbb_api_url: The url to your bigbluebutton instance (including the api/)
        :param salt: The security salt defined for your bigbluebutton instance
        :param meeting_name: A name for the meeting.
        :param meeting_id: A meeting ID that can be used to identify this meeting by the third party application.
                           This must be unique to the server that you are calling. If you supply a non-unique meeting ID,
                           you will still have a successful call, but will receive a warning message in the response.
                           If you intend to use the recording feature, the meetingID shouldn't contain commas.
        :param attendee_password: The password that will be required for attendees to join the meeting. 
                                  This is optional, and if not supplied, BBB will assign a random password.
        :param moderator_password:  The password that will be required for moderators to join the meeting or
                                    for certain administrative actions (i.e. ending a meeting). This is optional,
                                    and if not supplied, BBB will assign a random password.
        """
        self.bbb_api_url = bbb_api_url
        self.salt = salt
        self.meeting_name = meeting_name
        self.meeting_id = meeting_id
        self.attendee_password = attendee_password
        self.moderator_password = moderator_password

    def create_meeting(self):
        """
        creates the meeting
        """
        if not Meeting(self.bbb_api_url, self.salt).is_running(self.meeting_id):
            call = 'create'
            voicebridge = 70000 + random.randint(0, 9999)
            query = urlencode((
                ('name', self.meeting_name),
                ('meetingID', self.meeting_id),
                ('attendeePW', self.attendee_password),
                ('moderatorPW', self.moderator_password),
                ('voiceBridge', voicebridge),
                ('welcome', "Welcome!"),
            ))
            result = get_xml(self.bbb_api_url, self.salt, call, query)
            if result:
                return result
            else:
                raise


class Meeting(object):
    """
    gives access to meetings 
    """
    def __init__(self, bbb_api_url=None, salt=None):
        """
        :param bbb_api_url: The url to your bigbluebutton instance (including the api/)
        :param salt: The security salt defined for your bigbluebutton instance
        """
        self.bbb_api_url = bbb_api_url
        self.salt = salt

    def is_running(self, meeting_id):
        """
        This call enables you to simply check on whether or not a meeting is 
        running by looking it up with your meeting ID.
        
        :param meeting_id: ID that can be used to identify the meeting
        """
        call = 'isMeetingRunning'
        query = urlencode((
            ('meetingID', meeting_id),
        ))
        result = get_xml(self.bbb_api_url, self.salt, call, query)
        if result:
            return result.find('running').text == 'true'
        else:
            return 'error'
        
    def join_url(self, meeting_id, name, password):
        """
        generates the url for accessing a meeting 
        
        :param meeting_id: ID that can be used to identify the meeting
        :param name: The name that is to be used to identify this user to 
                     other conference attendees.
        :param password: The password that this attendee is using. 
                         If the moderator password is supplied, he will be 
                         given moderator status 
                         (and the same for attendee password, etc)
        """
        call = 'join'
        query = urlencode((
                           ('fullName', name),
                           ('meetingID', meeting_id),
                           ('password', password),
                           ))
        hashed = api_call(self.salt, query, call)
        url = self.bbb_api_url + call + '?' + hashed
        return url

    def end_meeting(self, meeting_id, password):
        """
        Use this to forcibly end a meeting and kick all participants out of the meeting.
        
        :param meetingID: The meeting ID that identifies the meeting you are attempting to end.
        :param password: The moderator password for this meeting.
                         You can not end a meeting using the attendee password.
        """
        call = 'end'
        query = urlencode((
                           ('meetingID', meeting_id),
                           ('password', password),
        ))
        result = get_xml(self.bbb_api_url, self.salt, call, query)
        if result:
            pass
        else:
            return 'error'

    def meeting_info(self, meeting_id, password):
        """
        This call will return all of a meeting's information, 
        including the list of attendees as well as start and end times.

        :param meetingID: The meeting ID that identifies the meeting you are 
                          attempting to end.
        :param password: The moderator password for this meeting.
                         You can not end a meeting using the attendee password.
        """
        call = 'getMeetingInfo'
        query = urlencode((
                           ('meetingID', meeting_id),
                           ('password', password),
                           ))
        r = get_xml(self.bbb_api_url, self.salt, call, query)
        if r:
            # Create dict of values for easy use in template
            d = {
                 'start_time': r.find('startTime').text,
                 'end_time': r.find('endTime').text,
                 'participant_count': r.find('participantCount').text,
                 'moderator_count': r.find('moderatorCount').text,
                 'moderator_pw': r.find('moderatorPW').text,
                 'attendee_pw': r.find('attendeePW').text,
                 'invite_url': 'join=%s' % meeting_id,
                 }
            return d
        else:
            return None

    def get_meetings(self):
        """
        This call will return a list of all the meetings found on this server.
        """
        call = 'getMeetings'
        query = urlencode((
                           ('random', 'random'),
                           ))

        result = get_xml(self.bbb_api_url, self.salt, call, query)
        if result:
            # Create dict of values for easy use in template
            d = []
            r = result[1].findall('meeting')
            for m in r:
                meeting_id = m.find('meetingID').text
                password = m.find('moderatorPW').text
                d.append({
                          'name': meeting_id,
                          'running': m.find('running').text,
                          'moderator_pw': password,
                          'attendee_pw': m.find('attendeePW').text,
                          'info': self.meeting_info(
                                               meeting_id,
                                               password)
                          })
            return d
        else:
            return 'error'

