import datetime
import pytz
import sys

class StyleFlagOnly():
	def __init__(self, url):
		# settings
		self.zd_url = url
		self.html = ''
		self.ticket = None
		self.timeformat = '%Y-%m-%d %H:%M'
		
		# the actual style
		self.ticket_subject_block	= 'margin: 0px; font-weight: bold; font-size: 18px; text-align: center; font-family: Arial, Helvetica, sans-serif; background-color: #FFFFFF'
		self.ticket_subject		= 'font-size: 18px; font-weight: bold'
		self.ticket_subtitle		= 'font-size: 12px; font-weight: normal'
		
		self.status_style		= {}
		self.status_style['Open']	= 'background: #F59993; border-radius: 3px; padding: 3px;'
		self.status_style['Pending']	= 'background: #A3AFFF; border-radius: 3px; padding: 3px;'
		self.status_style['Closed']	= 'background: #000000; color: #FFFFFF; border-radius: 3px; padding: 3px;'
		self.status_style['Solved']	= 'background: #C2C2C2; border-radius: 3px; padding: 3px;'
		self.status_style['Onhold']	= 'background: #FF00FF; border-radius: 3px; padding: 3px;'
		
		self.comment_table_style	= 'width: 100%; font-size: 12px;'
		
		self.comment_public		= []
		self.comment_private		= []
		self.comment_public.append("background-color: #F5F5F5; font-family: Arial, Helvetica, sans-serif")
		self.comment_public.append("background-color: #E5E5E5; font-family: Arial, Helvetica, sans-serif")
		self.comment_private.append("background-color: #FFFFDD; font-family: Arial, Helvetica, sans-serif")
		self.comment_private.append("background-color: #FFFFBB; font-family: Arial, Helvetica, sans-serif")
		self.comment_flagged		= 'background-color: #FFB5B5; font-family: Arial, Helvetica, sans-serif'

		self.comment_meta		= 'padding: 7px; width: 140px'
		self.comment_body		= 'padding: 7px'

	def startReport(self):
		self.ticket_index = 0
		self.html += '<html><head><meta http-equiv="Content-Type" content="text/html; charset=utf-8"><title>Zendesk Report</title></head><body>'
		
	def stopReport(self):
		self.html += '</body></html>'
		
	def startTicket(self, ticket):
		# track comment number for row coloring
		self.comment_index = 0
		
		# header block
		self.html += f'<p style="{self.ticket_subject_block}">{ticket.subject} - {ticket.assignee}'
		self.html += '<br />'
		self.html += f'<span style="{self.ticket_subtitle}">{ticket.type} <a href="{self.zd_url}/agent/tickets/{ticket.id}">{ticket.id}</a>'
		self.html += f' is <span style="{self.status_style[ticket.status]}">{ticket.status}</span>, '
		self.html += f'last updated at {ticket.last_updated.astimezone().strftime(self.timeformat)}</span></p>'
	
		# table start
		self.html += f'<table style="{self.comment_table_style}"><tbody>'
		# comment loop here...
		
	def stopTicket(self):
		self.html += '</tbody></table><br /><br />'
		
	def comment(self, comment):
		# track attachment count per comment
		self.attachment_index = 0
	
		# row
		if comment.flagged:
			self.html += f'<tr style="{self.comment_flagged}">'
		else:
			if comment.public:
				self.html += f'<tr style="{self.comment_public[self.comment_index % len(self.comment_public)]}">'
			else:
				self.html += f'<tr style="{self.comment_private[self.comment_index % len(self.comment_private)]}">'
		
		# user/date
		self.html += f'<td style="{self.comment_meta}"><a href="mailto:{comment.author}">{comment.author}</a><br />{comment.time.astimezone().strftime(self.timeformat)}</td>'
		
		# comment body
		self.html += f'<td style="{self.comment_body}>{comment.body}'
		
		# attachments
		for attachment in comment.attachments:
			self.html += f'<br /><p>Attachment {self.attachment_index}: <a href="{attachment.content_url}">{attachment.filename}</a></p>'
			self.attachment_index += 1
		
		self.html += '</td>'
		
		# close
		self.html += '</tr>'
		
		self.comment_index += 1

class ReportFlagonly():
	def __init__(self, zd, hours):
		self.zd		= zd
		self.hours	= hours
		self.report	= StyleFlagOnly((zd.url))
		
	def getReport(self):
		self.zd.searchRaw(f"updated>{self.hours}hour sort:desc order_by:updated_at type:ticket")
		now = datetime.datetime.utcnow()
		start_time = datetime.datetime(now.year, now.month, now.day,tzinfo=pytz.timezone('UTC')) - datetime.timedelta(hours=self.hours)
		
		# find rally tickets
		flagged = []
		for ticket in self.zd.tickets:
			if ticket.flagged:
				flagged.append(ticket)
				continue
			for comment in ticket.comments:
				if comment.flagged:
					flagged.append(ticket)
					break
		
		# normal comments
		self.report.startReport()
		for ticket in flagged:
			self.report.startTicket(ticket)
			for comment in ticket.comments:
				if comment.time >= start_time or True:
					self.report.comment(comment)
			self.report.stopTicket()
		self.report.stopReport()
						
		return(self.report.html)
		
