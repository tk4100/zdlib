import time
import datetime
import pytz
import pickle
import json
import requests

from zdesk import Zendesk

# Attachments and Attachment
class Attachment():
    def __init__(self, attachment):
        try:
            self.raw            = attachment
        
            self.id             = attachment['id']
            self.size           = attachment['size']
            self.filename       = attachment['file_name']
            self.content_url    = attachment['content_url']
        except KeyError as e:
            print("Failed to normalize attachment! {}".format(e))
            raise ValueError("Invalid attachment!")
        
    def dump(self):
        try:
            return(pickle.dumps(self))
        except Exception as e:
            print("Failed to dump attachment metadata! \"{}\"".format(e))
            return(False)
        
    def fetch(self):
        try:
            r = requests.get(self.content_url)
            return(r.content)
        except Exception as e:
            print("Failed to fetch attachment from {}! \"{}\"".format(e))
            return(False)
        
class Attachments():
    def __init__(self, attachments):
        self.attachments = []
        for attachment in attachments:
                self.attachments.append(Attachment(attachment))
    
    def __iter__(self):
        self.index = 0
        return(self)

    def __next__(self):
        if self.index < len(self.attachments):
            idx = self.index
            self.index += 1
            return(self.attachments[idx])
        else:
            raise StopIteration

    def __getitem__(self, index):
        if index >= len(self.attachments) * -1 and index < len(self.attachments):
            return(self.attachments[index])
        else:
            raise IndexError

# Comments and Comment
class Comment():
    def __init__(self, res, comment):
        try:
            self.raw        = comment
            self.id         = comment['id']
            self.time       = datetime.datetime.strptime(comment['created_at'], '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=pytz.timezone('UTC'))
            self.author_id  = int(comment['author_id'])
            self.author     = res.iddb.query(int(comment['author_id']))
            self.body       = comment['html_body']
            self.body_plain = comment['plain_body']
            self.public     = comment['public']
            self.metadata   = comment['metadata']

            # attachments are not always here
            if 'attachments' in comment.keys():
                self.attachments = Attachments(comment['attachments'])
                
            # check for rallycall flag
            if 'rallycall' in comment['html_body'].lower():
                self.flagged = True
            else:
                self.flagged = False
                
        except KeyError as e:
            print("Failed to normalize comment!  Exception: ", e, ", Raw data:\n\n", comment, "\n\n")

    def dump(self):
        dump = self.raw
        
        # or else every ticket dump contains every comment dump which contains every attachment dump
        if 'attachments' in dump.keys():
            del(dump['attachments'])
        
        try:
            return(pickle.dumps(dump))
        except Exception as e:
            print("Failed to dump comment! \"{}\"".format(e))
            return(False)


class Comments():
    def __init__(self, res, ticket_id):
        self.res = res
        self.ticket = ticket_id

        # internals
        self.fetch_timestamp = 0
        self.all_fetched = False
        self.comments = []
        self.index = 0
        self.page = 1

    def ageCache(self):
        if self.fetch_timestamp - time.time() > 480:
            self.comments = []
            self.index = 0
            self.page = 1
            self.all_fetched = False
            self.fetch_timestamp = time.time()

    def fetchMore(self):
        if self.all_fetched:
            return(False)
        try:
            new = self.res.zd.ticket_comments(self.ticket, page=self.page)
            self.comments += [ Comment(self.res, x) for x in new['comments'] ]
            # set flags if there are no more comments to fetch.
            if new['next_page'] == None:
                self.all_fetched = True
            else:
                self.page += 1
            return(True)
        except IndexError as e:
            print("Error retrieving page {} of comments for ticket {}. \"{}\"".format(self.page, self.ticket, e))
            return(False)
       

    def __iter__(self):
        self.index = 0
        self.page = 1

        self.ageCache()

        return(self)

    def __next__(self):
        # first just try and fulfill from cache
        try:
            r = self.comments[self.index]
            self.index += 1
            return(r)
        # if we can get more comments get them and recurse.  If not, StopIteration.
        except IndexError:
            if self.fetchMore():
                return(self.__next__())
            else:
                raise StopIteration
                

    # direct fetching, not so efficient
    def __getitem__(self, index):
        self.ageCache()
    
        try:
            return(self.comments[index])
        except IndexError:
            # fetch until we have the comment, or we run out of comments
            while index >= len(self.comments) and not self.all_fetched:
                self.fetchMore()

            # try again and raise IndexError on fail this time
            try:
                return(self.comments[index])
            except IndexError:
                raise IndexError("There are not that many comments you tool!")

class Ticket():
    def __init__(self, res, ticket):
        try:
            self.raw           = ticket
            self.id            = int(ticket['id'])
            self.type	       = ticket['type']
            self.assignee      = res.iddb.query(ticket['assignee_id'])
            self.subject       = ticket['raw_subject']
            self.last_updated  = datetime.datetime.strptime(ticket['updated_at'], '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=pytz.timezone('UTC'))
            self.status        = ticket['status'].capitalize()
            self.tags          = ticket['tags']
            self.create_date   = datetime.datetime.strptime(ticket['created_at'], '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=pytz.timezone('UTC'))
            self.via           = ticket['via']['channel']
            self.requester     = res.iddb.query(int(ticket['requester_id']))
            self.requester_id  = int(ticket['requester_id'])
            self.comments      = Comments(res, self.id)
            self.flagged = False
            for tag in self.tags:
            	if 'rallycall' in tag.lower():
            		self.flagged = True
        except KeyError as e:
            raise ValueError("Failed to normalize ticket!\n\n", "Exception:\n\n", e, "\n\nRaw data:\n\n", ticket, "\n\n")

    def dump(self):
        dump = self.raw
        
        # or else every ticket dump contains every comment dump which contains every attachment dump
        if 'comments' in dump.keys():
            del(dump['comments'])
        
        try:
            return(pickle.dumps(dump))
        except Exception as e:
            print("Failed to dump comment! \"{}\"".format(e))
            return(False)

class Tickets():
    # init and connect to ZD
    def __init__(self, res, query):
        self.res = res
        self.query = query + " type:ticket"

        # internals
        self.fetch_timestamp = 0
        self.all_fetched = False
        self.tickets = []
        self.page = 1
        self.index = 0
        
    def ageCache(self):
        if self.fetch_timestamp - time.time() > 480:
            self.tickets = []
            self.index = 0
            self.page = 1
            self.all_fetched = False
            self.fetch_timestamp = time.time()
        
    def fetchMore(self):
        if self.all_fetched:
            return(False)
        try:
            new = self.res.zd.search(query=self.query, page=self.page)
            self.tickets += [ Ticket(self.res, x) for x in new['results'] ]
            # set flags if there are no more tickets to fetch.
            if new['next_page'] == None:
                self.all_fetched = True
            else:
                self.page += 1
            return(True)
        except Exception as e:
            print("Error retrieving page {} of results for search \"{}\". \"{}\"".format(self.page, self.query, e))
            return(False)

    def __iter__(self):
        self.index = 0
        self.page = 1

        self.ageCache()

        return(self)

    def __next__(self):
        # first just try and fulfill from cache
        try:
            r = self.tickets[self.index]
            self.index += 1
            return(r)
        # if we can get more tickets get them and recurse.  If not, StopIteration.
        except IndexError:
            if self.fetchMore():
                return(self.__next__())
            else:
                raise StopIteration

    # direct fetching, not so efficient
    def __getitem__(self, index):
        self.ageCache()
    
        try:
            return(self.tickets[index])
        except IndexError:
            # fetch until we have the comment, or we run out of comments
            while index >= len(self.tickets) and not self.all_fetched:
                self.fetchMore()

            # try again and raise IndexError on fail this time
            try:
                return(self.tickets[index])
            except IndexError:
                raise IndexError("There are not that many comments you tool!")

class IDDB():
    def __init__(self, zd):
        self.zd = zd
        self.iddb_path = '/tmp/zdlib2_iddb_cache.db'
        
        try:
            with open(self.iddb_path, 'rb') as iddb:
                self.iddb = pickle.load(iddb)
        except IOError:
            self.iddb = {}
            self.flush()
        except EOFError:
            self.iddb = {}
            self.flush()

    def flush(self):
        try:
            with open(self.iddb_path, 'wb') as iddb:
                pickle.dump(self.iddb, iddb, pickle.HIGHEST_PROTOCOL)
        except Exception as e:
            raise IOError("Error writing IDDB!!! \"{}\"".format(e))
            
    def query(self, author_id):
        # if the value is None, return "unassigned".  Comments can never not have an author.
        if author_id == None:
            return("Unassigned")

        try:
            author_id = int(author_id)
        except:
            print("ID {} is not a number.".format(author_id))
            return(False)

        # return from cache if possible, checking time and updating old records
        if author_id in self.iddb.keys():
            if self.iddb[author_id]['timestamp'] > datetime.datetime.now() - datetime.timedelta(days=1):
                return(self.iddb[author_id]['email'])
            else:
                del(self.iddb[author_id])

        # if not, add it.
        try:
            raw_ids = self.zd.user_identities(author_id)
        except Exception as e:
            #print("Failed to resolve author_id \"{}\"! ({})".format(author_id, e))
            return("User not found!")
            
        for raw_id in raw_ids['identities']:
            if raw_id['primary'] == True and raw_id['type'] == 'email':
                self.iddb[author_id] = { 'email' : raw_id['value'], 'timestamp' : datetime.datetime.now() }
                self.flush()
                return(raw_id['value'])

        # not found : (
        return("User not found!")
        
class Resources():
    def __init__(self, zd, iddb):
        self.zd = zd
        self.iddb = iddb  
      
class ZD():
    # a ticket class
    
    # BACK TO ZD OBJ
    def __init__(self, url, username, api_token):
        # organize into a ZDesk friendly format
        creds = {
            'zdesk_email'       : username,
            'zdesk_password'    : api_token,
            'zdesk_url'         : url,
            'zdesk_token'       : True
            }

        # gather resources
        zd = Zendesk(**creds)
        iddb = IDDB(zd)
        self.res = Resources(zd, iddb)

    # search wrappers
    def searchCreateDate(self, start, end=False):
        pass

    def searchUpdateDate(self, start, end=False):
        pass

    def searchRaw(self, query):
        self.tickets = Tickets(self.res, query)
    


    
