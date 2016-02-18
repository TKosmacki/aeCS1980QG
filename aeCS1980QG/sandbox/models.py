#import datetime
import logging
import os
import webapp2
import mimetypes
#import json
from google.appengine.api import images
from google.appengine.ext.webapp import template
from google.appengine.api import users
from google.appengine.ext import ndb
from google.appengine.api import memcache
from google.appengine.ext import blobstore
from google.appengine.ext.webapp import blobstore_handlers


class global_id(ndb.Model):
	next_id = ndb.IntegerProperty()

	def increase_id(self):
		self.next_id = self.next_id + 1

class user_profile(ndb.Model):
	user_id = ndb.StringProperty()
	firstname = ndb.StringProperty()
	lastname = ndb.StringProperty()
	username = ndb.StringProperty()
	classID = ndb.StringProperty()
	location = ndb.StringProperty()

class question_obj(ndb.Model):
    category = ndb.StringProperty()
    question = ndb.StringProperty()
    answer1 = ndb.StringProperty()
    answer2 = ndb.StringProperty()
    answer3 = ndb.StringProperty()
    answer4 = ndb.StringProperty()
    answerid = ndb.StringProperty()
    create_datetime = ndb.DateTimeProperty(auto_now_add=True)
    score = ndb.IntegerProperty(default=0)
    creator = ndb.StringProperty(default="user")

def update_profile(id, firstname, lastname, username, classID, location):
	profile = get_user_profile(id)
	profile.populate(firstname = firstname, lastname = lastname, username = username, classID = classID, location = location)
	profile.put()
	
	memcache.set(id, profile, namespace="profile")


def create_profile(id):
	profile = user_profile()
	profile.user_id = id
	profile.key = ndb.Key(user_profile,id)
	profile.put()

	memcache.set(id, profile, namespace="profile")

def check_if_user_profile_exists(id):
	result = list()
	q = user_profile.query(user_profile.user_id == id)
	q = q.fetch(1)

	##if q == []:
	return q

def get_user_profile(id):
	result = memcache.get(id, namespace="profile")
	if not result:
		result = ndb.Key(user_profile, id).get()
		memcache.set(id, result, namespace="profile")
	return result

def create_global_id():
	id = ndb.Key(global_id, "number").get()
	#logging.warning(id)
	if id == None:
		id = global_id()
		id.next_id = 1
		id.key = ndb.Key(global_id, "number")
		id.put()
		memcache.set("number", id, namespace="global_id")

def create_question(category,question,answer1,answer2,answer3,answer4,answerid):
    question_number = create_global_id()
    question = question_obj(category=category,
        question=question,
        answer1=answer1,
        answer2=answer2,
        answer3=answer3,
        answer4=answer4,
        answerid=answerid)
    question.key = ndb.Key(question_obj, question_number)
    question.put()

    return question_number
    
def get_oldest_questions(num):
    query= question_obj.query()
    query.order(question_obj.create_datetime)
   
    return query.fetch(num)
