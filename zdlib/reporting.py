class StyleFlagOnly():
	def __init__(self, url):
		# settings
		self.zd_url = url
		self.html = ''
		self.ticket = None
		
		# the actual style
		self.ticket_subject_block	= 'margin: 0px; text-align: center; font-family: Arial, Helvetica, sans-serif; background-color: #FFFFFF'
		self.ticket_subject		= 'font-size: 18px; font-weight: bold'
		self.ticket_subtitle		= 'font-size: 12px; font-weight: normal'
		
		self.status_style['Open']	= 'background: #F59993; border-radius: 5px; padding: 5px;'
		self.status_style['Pending']	= 'background: #A3AFFF; border-radius: 5px; padding: 5px;'
		self.status_style['Closed']	= 'background: #000000; font-color: #FFFFFF: border-radius: 5px; padding: 5px;'
		self.status_style['Solved']	= 'background: #C2C2C2; border-radius: 5px; padding: 5px;'
		self.status_style['Onhold']	= 'background: #FF00FF; border-radius: 5px; padding: 5px;'
		
		self.comment_table_style	= 'width: 100%; font-size: 12px;'
		
		self.comment_public		= []
		self.comment_private		= []
		self.comment_public.append("background-color: #F5F5F5; font-family: Arial, Helvetica, sans-serif" ]
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
		self.html += f'<p style="{self.ticket_subject_block}>{ticket.subject} - {ticket.assignee}</p>'
		self.html += '<br />'
		self.html += f'<span style="{self.ticket_subtitle}">{ticket.type} <a href="{self.zd_url}/agent/tickets/{ticket.id}>{ticket.id}</a>'
		self.html += f' is <span style="{self.status_style['ticket.status']}">{ticket.status}</span>, '
		self.html += f'last updated at {ticket.last_updated}</span></p>'
	
		# table start
		self.html += f'<table style="{self.comment_table_style}"><tbody>'
		# comment loop here...
		
	def stopTicket(self):
		self.html += '</tbody></table><br /><br />'
		
	def comment(self, comment):
		# row
		if comment.flagged:
			self.html += f'<tr style="{self.comment_flagged}>"
		else:
			if comment.public:
				self.html += f'<tr style="{self.comment_public[self.comment_index % len(self.comment_public)]}>"
			else:
				self.html += f'<tr style="{self.comment_private[self.comment_index % len(self.comment_private)]}>"
		
		# user/date
		self.html += f'<td style="{self.comment_meta}"><a href="mailto:{comment.author}">{comment.author}</a><br />'
		self.html += f'{comment.time}</td>'
		
		# comment body
		self.html += f'<td style="{self.comment_body}>{comment.body}</td>
		
		# close
		self.html += '</tr>'
		
		self.comment_index += 1

class Report():
	def __init__(self, zd):
		self.zd		= zd
		self.report	= StyleFlagOnly((zd))
		
	def getReport(self, start, end):
		
