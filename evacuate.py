import os
import sys
import time
import datetime
import mgzip
import requests
import pickle
from zdlib2 import ZD

# output
out_dir = "data2"
resumefile = "{}/resume.pickle".format(out_dir)
max_resumefile_age = 7 * 24 * 60 * 60 * 60

# connect
zd = ZD('https://<yourdomain>.zendesk.com', '<youremail>', '<yourkey>')

# pick up where we left off
window_start = datetime.datetime.now()
increment = datetime.timedelta(days=30)
if os.path.exists(resumefile):
    with open(resumefile, 'rb') as fh:
        resume = pickle.load(fh)
    if time.time() - resume['timestamp'] < max_resumefile_age:
        window_start = resume['start']
        increment = resume['increment'] 
else:
    resume = {}
window_end = window_start - increment

# debug
#window_start = datetime.datetime(2017, 1, 1)
#window_end = window_start - increment

# cutoff
end = datetime.datetime(2009,4,1)

# gather all interesting tickets
while window_start >= end:
    zd.searchRaw("created>={}-{}-{} created<={}-{}-{} order_by:created_at sort:desc".format(window_end.year, window_end.month, window_end.day, window_start.year, window_start.month, window_start.day))

    for ticket in zd.tickets:
        sys.stdout.write("\r\r\r\r\r\r\r\r\r\r\r\r\r\r\r\r\r\r\r\r\r\r\r\r\r\r\r\r\r\r\r\r\r\r\r\r\r\r\r\r\r\r\rLoading #{}...".format(ticket.id))
        sys.stdout.flush()
         
        ticket_dump = ticket.dump()
        while not ticket_dump:
            time.sleep(0.5)
            ticket_dump = ticket.dump()
         
        ticket_file = "{}/{}/ticket.gz".format(out_dir, ticket.id)
        if not os.path.exists("{}/{}".format(out_dir, ticket.id)):
            os.mkdir("{}/{}".format(out_dir, ticket.id))
            os.mkdir("{}/{}/comments".format(out_dir, ticket.id))
            os.mkdir("{}/{}/attachments".format(out_dir, ticket.id))
        if not os.path.exists(ticket_file):
            with open(ticket_file, 'wb') as fh:
                fh.write(mgzip.compress(ticket_dump))
            
        for comment in ticket.comments:
            comment_dump = comment.dump()
            while not comment_dump:
                time.sleep(0.5)
                comment_dump = comment.dump()
                
            comment_file = "{}/{}/comments/{}.gz".format(out_dir, ticket.id, comment.id)
            if not os.path.exists(comment_file):
                with open(comment_file, 'wb') as fh:
                    fh.write(mgzip.compress(comment_dump))
            
            for attachment in comment.attachments:
                attachment_file = "{}/{}/attachments/{}.gz".format(out_dir, ticket.id, attachment.filename.replace('/', '_'))
                if not os.path.exists(attachment_file):
                    with open(attachment_file, 'wb') as fh:
                        rq = requests.get(attachment.content_url)
                        if rq.ok:
                            fh.write(mgzip.compress(rq.content, compresslevel=5, thread=6))

    window_start = window_end
    window_end -= increment
    
    resume['start'] = window_start
    resume['increment'] = increment
    resume['timestamp'] = time.time()
    with open(resumefile, 'wb') as fh:
        pickle.dump(resume, fh)
    print("\n{} - Passed restore point!".format(datetime.datetime.now().strftime('%H:%M:%S')))
    
