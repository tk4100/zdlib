ZDLib is my attempt at a library interfacing with Zendesk in a way that I like. It's unfinished as of now, like so much software. evacuate.py is a quick-n-dirty tool for exporting all tickets/comments/attachments from Zendesk.

Yes:
1. Exporting tickets as raw JSON strings.
1. Exporting everything from Zendesk (not contacts yet).
1. Handling attachments.
1. Caching of certain repetitive details.

No:
1. Typing brackets and quotes until your fingers fall off.
1. Data I don't need attached to tickets.
1. Paging.
1. Manual retrying.

Maybe:
1. More efficent searching.
1. Integrated Dump-My-Zendesk(tm) feature for evacuations.
1. Rate limiting.
