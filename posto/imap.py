import imaplib
import email
import io
import re
import os
from . import imap_utf7
from . import slugify
from . import *

def init(host, user, password, port=993):
	mail = imaplib.IMAP4_SSL(host, port=port)
	status = mail.login(user, password)
	return mail

def ls(mail):
	result, data = mail.list()
	if result != "OK":
		raise Exception(data[0].decode("ascii"))
	
	ret = {}
	for folder in data:
		folder = imap_utf7.decode(folder).split("\"")
		folder.remove(" ")
		folder.remove("")
		sf = re.sub(r"\\HasChildren|\\HasNoChildren|[\(\)\\]", "", folder[0]).strip()
		if sf:
			ret[slugify.slugify(sf)] = folder[2]
		else:
			ret[slugify.slugify(folder[2])] = folder[2]

	return ret

def select(mail, folder):
	result, data = mail.select(imap_utf7.encode("\"{}\"".format(folder)))
	if result != "OK":
		raise Exception("{}".format(data[0].decode("ascii")))

def close(mail):
	if mail.state == "SELECTED":
		result, data = mail.close()
		if result != "OK":
			raise Exception(data[0].decode("ascii"))

# Use term "UID N:*" to search all email with uid >= N
def search(mail, term="ALL"):
	result, data = mail.uid("search", None, term)
	if result != "OK":
		raise Exception(data[0].decode("ascii"))
	
	for uid in data[0].split():
		yield int(uid)

def fetch(mail, uid, rfc="(RFC822)"):
	result, data = mail.uid("fetch", str(uid).encode(), rfc)
	if result != "OK":
		raise Exception(data[0].decode("ascii"))

	msg = email.message_from_bytes(data[0][1])
	return msg_parse(msg)

def logout(mail):
	result, data = mail.logout()
	if result != "BYE":
		raise Exception(data[0].decode("ascii"))

def write(msg, outf, attachments):
	outf.write("From: {From}\nTo: {To}\nCc: {Cc}\nDate: {Date}\nSubject: {Subject}\n\n".format(**msg[0]))
	outf.write(msg[1])

	if msg[2]:
		outf.write("\nAttachments:")
		for f in msg[2].keys():
			attachments = os.path.join(attachments, f)
			outf.write(" ~/{}".format(os.path.relpath(attachments, start=os.environ["HOME"])))
			open(os.path.join(attachments), "wb").write(msg[2][f].read())
	outf.write("\n")

class Mail:
	def __init__(self, host, user, password, port=993):
		self.mail = init(host, user, password, port=port)
		self.folders = ls(self.mail)

	def __del__(self):
		close(self.mail)
		logout(self.mail)

	def ls(self):
		return list(self.folders.keys())

	def select(self, folder):
		close(self.mail)
		select(self.mail, self.folders[folder])

	def search(self, term="ALL"):
		return search(self.mail, term=term)

	def fetch(self, uid, rfc="(RFC822)"):
		return fetch(self.mail, uid, rfc=rfc)