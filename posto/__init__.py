import email
import io
import re
import os
from .slugify import slugify
from datetime import datetime
from dateutil import tz
from sys import stderr

DT_FORMATS = ("%a, %d %b %Y %H:%M:%S %z",
			  "%a, %d %b %Y %H:%M:%S",
			  "%d %b %Y %H:%M:%S %z",
			  "%d %b %Y %H:%M:%S")

def encoding_get(encoding):
	if (encoding != None) and (encoding != "unknown-8bit"):
		return encoding
	else:
		return "utf-8"

def header_decode(sl):
	ret = ""
	for s in email.header.decode_header(sl):
		try:
			ret += s[0].decode(encoding_get(s[1]), errors="ignore")
		except AttributeError:
			ret += s[0]
	return ret

def headers_decode(emsg):
	ret = {}
	for key in emsg.keys():
		ret[key] = header_decode(emsg[key]).replace("\n", "")
	return ret

def date_parse(date):
# Fuck humans!
	date = re.sub(r" \(*[A-Z]{2,}\)*", "", date)
	date = re.sub(r"[\n\r]*", "", date)
	date = date.strip()
	for fmt in DT_FORMATS:
		try:
			return datetime.strptime(date, fmt)
		except ValueError:
			pass

def headers_shape(headers):
	if not "Subject" in headers.keys():
		headers["Subject"] = ""
	else:
		headers["Subject"] = re.sub(r"[\n\r]+", " ", headers["Subject"])

	if not "Date" in headers.keys():
		headers["Date"] = datetime.utcnow()
	else:
		headers["Date"] = date_parse(headers["Date"])

	if not "To" in headers.keys():
		headers["To"] = ""

	if not "From" in headers.keys():
		headers["From"] = ""

	if not "Cc" in headers.keys():
		headers["Cc"] =  ""

	return headers

def msg_shape(emsg):
	body = ""
	attachments = {}
	for m in emsg.walk():
		if (m.get_content_disposition() == "attachment") and (m.get_content_type() != "message/rfc822"):
			attachments[m.get_filename()] = io.BytesIO()
			attachments[m.get_filename()].write(m.get_payload(decode=True))
			attachments[m.get_filename()].seek(0)
		elif (m.get_content_type() == "text/plain"):
			body += m.get_payload(decode=True).decode(encoding_get(m.get_charsets()[0]), errors="ignore").replace("\r\n", "\n")
	if body == "":
		for m in emsg.walk():
			if m.get_content_maintype() == "text":
				body += m.get_payload(decode=True).decode(encoding_get(m.get_charsets()[0]), errors="ignore").replace("\r\n", "\n")

	return headers_shape(headers_decode(emsg)), body, attachments

def msg_dump(msg, outf, attachments):
	msg[0]["Date"] = msg[0]["Date"].isoformat()
	outf.write("From: {From}\nTo: {To}\nCc: {Cc}\nDate: {Date}\nSubject: {Subject}\nAttachments:".format(**msg[0]))
	
	if msg[2]:
		os.makedirs(attachments, exist_ok=True)
		for f in msg[2].keys():
			fpath = os.path.join(attachments, slugify(header_decode(f)))
			outf.write(" ~/{}".format(os.path.relpath(fpath, start=os.environ["HOME"])))
			open(fpath, "wb").write(msg[2][f].read())
	
	outf.write("\n\n{}\n".format(msg[1]))