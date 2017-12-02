import imaplib
import email
import io
import re
import os
from . import imap_utf7
from .slugify import slugify
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
	for mbox in data:
		mbox = imap_utf7.decode(mbox).split("\"")
		mbox.remove(" ")
		mbox.remove("")
		sf = re.sub(r"\\HasChildren|\\HasNoChildren|[\(\)\\]", "", mbox[0]).strip()
		if sf:
			ret[slugify(sf)] = mbox[2]
		else:
			ret[slugify(mbox[2])] = mbox[2]

	return ret

def select(mail, mbox):
	result, data = mail.select(imap_utf7.encode("\"{}\"".format(mbox)))
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
	return msg_shape(msg)

def logout(mail):
	result, data = mail.logout()
	if result != "BYE":
		raise Exception(data[0].decode("ascii"))

class Mail:
	def __init__(self, host, user, password, port=993):
		self.mail = init(host, user, password, port=port)
		self.mboxes = ls(self.mail)

	def __del__(self):
		close(self.mail)
		logout(self.mail)

	def ls(self):
		return list(self.mboxes.keys())

	def select(self, mbox):
		close(self.mail)
		select(self.mail, self.mboxes[mbox])

	def search(self, term="ALL"):
		return search(self.mail, term=term)

	def fetch(self, uid, rfc="(RFC822)"):
		return fetch(self.mail, uid, rfc=rfc)