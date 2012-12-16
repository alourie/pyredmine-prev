import urllib
import urllib2
import xml.etree.ElementTree as ET


class _Project:
    '''Object returned by Redmine getProject calls
       redmine is the redmine object.
       objPr is the json object containing the project data'''

    def __init__(self, redmine):
        self.__redmine = redmine
        self.description = None
        self.homepage = None
        self.id = None
        self.name = None
        self.createdon = None
        self.updateon = None

    def newIssue(self, **data):
        '''Create a new issue for this project from the given values.

        newIssue(subject="The Arguments Department is closed",
                 description="Good morning.",
                 )

        Possible keys are:
         subject
         description
         status_id
         priority_id
         tracker_id - can be looked up from name in Project.trackers[name],
            basically an issue type (bug, feature, etc)
         assigned_to_id

        Unfortunately, there is no easy way to discover the valid values
        for most of the _id fields'''

        print "Got params: %s" % data

        if not 'subject' in data.keys():
            raise TypeError('Subject field cannot be blank.'
                            ' Use newIssue(subject=str) to create a new issue.')

        # TODO: what is the project_id ?? Should be initialized, of course
        data['project_id'] = self.id
        return self.__redmine.newIssueFromDict(data)

    def getIssues(self):
        pass
        #todo: finish


class _Issue:
    '''Object returned by Redmine getIssue and newIssue calls'''
    def __init__(self, redmine, data):
        self.__redmine = redmine

        self.id = None
        self.subject = None
        self.custom = {}
        self.relations = {}
        self.assigned_to = None
        self.tracker = None
        self.status = None
        self.description = None

        if data:
            try:
                self.parseData(data)
            except:
                raise

    def parseData(self, data):
        '''Parse fields from given Issue object'''

        # TODO: actually parse the Issue data object
        self.id        = self.root.find('id').text
        self.project   = self.root.find('project').attrib
        self.tracker   = self.root.find('tracker').attrib
        self.status    = self.root.find('status').attrib
        self.priority  = self.root.find('status').attrib
        self.author    = self.root.find('status').attrib
        self.assigned_to = self.root.find('status').attrib
        self.subject   = self.root.find('subject').text
        self.description = self.root.find('description').text
        self.start_date = self.root.find('description').text
        self.due_date = self.root.find('description').text
        self.done_ratio = self.root.find('description').text
        self.estimated_hours = self.root.find('description').text
        self.spent_hours = self.root.find('description').text
        self.created_on = self.root.find('description').text
        self.update_on = self.root.find('description').text


    def resolve(self):
        '''Resolve this issue'''
        self.__redmine.resolveIssue(self.id)

    def close(self):
        '''Close this issue'''
        self.__redmine.closeIssue(self.id)

    def save(self):
        '''Saves this issue - updates or creates new issue as necessary.  Failed updates DO NOT return any errors.'''
        pass


class Redmine:
    '''Class to interoperate with a Redmine installation using the REST web services.
    instance = Redmine(url, [key=strKey], [username=strName, password=strPass])

    url is the base url of the Redmine install ( http://my.server/redmine)

    key is the user API key found on the My Account page for the logged in user
        All interactions will take place as if that user were performing them, and only
        data that that user can see will be seen

    If a key is not defined then a username and password can be used
    If neither are defined, then only publicly visible items will be retreived
    '''

    def __init__(self, url, key=None, username=None, password=None, debug=False, readonlytest=False):
        self.__url = url
        self.__key = key
        self.debug = debug
        self.readonlytest = readonlytest
        self.projects = {}
        self.projectsID = {}
        self.issuesID = {}

        # Status ID from a default install
        self.ISSUE_STATUS_ID_NEW = 1
        self.ISSUE_STATUS_ID_RESOLVED = 3
        self.ISSUE_STATUS_ID_CLOSED = 5

        if readonlytest:
            print 'Redmine instance running in read only test mode.  No data will be written to the server.'

        self.__opener = None

        if not username:
            username = key
            self.__key = None

        if not password:
            password = '12345'  # the same combination on my luggage!  (dummy value)

        if username and password:
            #realm = 'Redmine API'
            # create a password manager
            password_mgr = urllib2.HTTPPasswordMgrWithDefaultRealm()

            password_mgr.add_password(None, url, username, password)
            handler = urllib2.HTTPBasicAuthHandler(password_mgr)

            # create "opener" (OpenerDirector instance)
            self.__opener = urllib2.build_opener(handler)

            # set the opener when we fetch the URL
            self.__opener.open(url)

            # Install the opener.
            urllib2.install_opener(self.__opener)

        else:
            if not key:
                pass
                #raise TypeError('Must pass a key or username and password')

    def Issue(self, data):
        '''Issue object factory'''
        return _Issue(self, data)

    def Project(self, data):
        '''Project obect factory'''
        return _Project(self, data)

    # extend the request to handle PUT command
    class PUT_Request(urllib2.Request):
        def get_method(self):
            return 'PUT'

    # extend the request to handle DELETE command
    class DELETE_Request(urllib2.Request):
        def get_method(self):
            return 'DELETE'

    def openRaw(self, page, parms=None, XMLstr=None, HTTPrequest=None, dict=None):
        '''Opens a page from the server with optional XML.  Returns a response file-like object'''
        if not parms:
            parms = {}

        # if we're using a key, add it to the parms array
        if self.__key:
            parms['key'] = self.__key

        # encode any data
        urldata = ''
        if parms:
            urldata = '?' + urllib.urlencode(parms)

        fullUrl = self.__url + '/' + page

        # register this url to be used with the opener
        if self.__opener:
            self.__opener.open(fullUrl)

        #debug
        if self.debug:
            print fullUrl + urldata

        # Set up the request
        if HTTPrequest:
            request = HTTPrequest(fullUrl + urldata)
        else:
            request = urllib2.Request(fullUrl + urldata)
        # get the data and return XML object or Json
        if XMLstr:
            request.add_header('Content-Type', 'application/xml')
            response = urllib2.urlopen(request, XMLstr)
        elif dict:
            request.add_header('Content-Type', 'application/json')
            response = urllib2.urlopen(request, urllib.urlencode(dict))
        else:
            response = urllib2.urlopen(request)

        if self.debug:
            print "Response is:\n %s\n" % response
        return response

    def open(self, page, parms=None, objXML=None, HTTPrequest=None, dict=None):
        '''Opens a page from the server with optional XML.  Returns an XML ETree object or string if return value isn't XML'''
        response = self.openRaw(page, parms, objXML, HTTPrequest, dict)
        try:
            etree = ET.ElementTree()
            etree.parse(response)
            return etree
        except:
            return response.read()

    def get(self, page, parms=None):
        '''Gets a JSON object from the server - used to read Redmine items.'''
        return self.open(page, parms)

    def post(self, page, objJSON, parms=None):
        '''Posts a JSON object to the server - used to make new Redmine items.  Returns an XML object.'''
        if self.readonlytest:
            print 'Redmine read only test: Pretending to create: ' + page
            return objJSON
        else:
            return self.open(page=page, parms=parms, dict=objJSON)

    def put(self, page, objJSON, parms=None):
        '''Puts a JSON object on the server - used to update Redmine items.  Returns nothing useful.'''
        if self.readonlytest:
            print 'Redmine read only test: Pretending to update: ' + page
        else:
            return self.open(page, parms, objJSON, HTTPrequest=self.PUT_Request)

    def delete(self, page):
        '''Deletes a given object on the server - used to remove items from Redmine.  Use carefully!'''
        if self.readonlytest:
            print 'Redmine read only test: Pretending to delete: ' + page
        else:
            return self.open(page, HTTPrequest=self.DELETE_Request)

    def dict2XML(self, tag, dict):
        '''Return an XML string encoding the given dict'''
        root = ET.Element(tag)
        for key in dict:
            ET.SubElement(root, str(key)).text = str(dict[key])

        return ET.tostring(root, encoding='UTF-8')

    def getProject(self, projectIdent):
        '''returns a JSON project object for the given project name'''
        return self.Project(self.get('projects/' + projectIdent + '.json'))

    def getIssue(self, issueID):
        '''returns a JSON issue object for the given issue number'''
        return self.Issue(self.get('issues/' + str(issueID) + '.json'))

    def newIssueFromDict(self, dict):
        '''creates a new issue using fields from the passed dictionary.  Returns the issue number or None if it failed. '''
        #xmlStr = self.dict2XML( 'issue', dict)
        #print "xmlStr is \n%s\n" % xmlStr
        newIssue = self.Issue(self.post('issues.json', dict))
        return newIssue

    def updateIssueFromDict(self, ID, dict):
        '''updates an issue with the given ID using fields from the passed dictionary'''
#        xmlStr = self.dict2XML('issue', dict)
        self.put('issues/' + str(ID) + '.json', dict)

    def deleteIssue(self, ID):
        '''delete an issue with the given ID.  This can't be undone - use carefully!
        Note that the proper method of finishing an issue is to update it to a closed state.'''
        self.delete('issues/' + str(ID) + '.xml')

    def closeIssue(self, ID):
        '''close an issue by setting the status to self.ISSUE_STATUS_ID_CLOSED'''
        self.updateIssueFromDict(ID, {'status_id': self.ISSUE_STATUS_ID_CLOSED})

    def resolveIssue(self, ID):
        '''close an issue by setting the status to self.ISSUE_STATUS_ID_RESOLVED'''
        self.updateIssueFromDict(ID, {'status_id': self.ISSUE_STATUS_ID_RESOLVED})

