#import datetime
import logging
import os
import webapp2
#import json
from google.appengine.ext.webapp import template
from google.appengine.api import users
from google.appengine.ext import ndb
from google.appengine.api import memcache


class global_id(ndb.Model):
	next_id = ndb.IntegerProperty()

	def increase_id(self):
		self.next_id = self.next_id + 1

class user_profile(ndb.Model):
	user_id = ndb.StringProperty()
	name = ndb.StringProperty()
	location = ndb.StringProperty()
	interests = ndb.StringProperty()

class question_obj(ndb.Model):
    id = ndb.IntegerProperty()
    category = ndb.StringProperty()
    question = ndb.StringProperty()
    answer1 = ndb.StringProperty()
    answer2 = ndb.StringProperty()
    answer3 = ndb.StringProperty()
    answer4 = ndb.StringProperty()
    answerid = ndb.StringProperty()
    correctAnswers = ndb.IntegerProperty(default=0)
    incorrectAnswers = ndb.IntegerProperty(default=0)
    answer1Selections = ndb.IntegerProperty(default=0)
    answer2Selections = ndb.IntegerProperty(default=0)
    answer3Selections = ndb.IntegerProperty(default=0)
    answer4Selections = ndb.IntegerProperty(default=0)
    create_datetime = ndb.DateTimeProperty(auto_now_add=True)
    score = ndb.IntegerProperty(default=0)
    creator = ndb.StringProperty(default="user")

def update_profile(id, name, location, interests):
	profile = get_user_profile(id)
	profile.populate(name = name, location = location, interests = interests)
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

class global_id(ndb.Model):
    next_id = ndb.IntegerProperty()

    def increase_id(self):
        self.next_id = self.next_id + 1
        
def get_global_id():
    id = memcache.get("number", namespace="global_id")
    if not id:
        id = ndb.Key(global_id, "number").get()
    logging.warning(id)
    value = id.next_id
    id.increase_id()
    id.put()
    memcache.set("number", id, namespace="global_id")
    return value
    
def create_global_id():
	id = ndb.Key(global_id, "number").get()
	logging.warning(id)
	if id == None:
		id = global_id()
		id.next_id = 1
		id.key = ndb.Key(global_id, "number")
		id.put()
		memcache.set("number", id, namespace="global_id")

def create_question(category,question,answer1,answer2,answer3,answer4,answerid):
    question_number = get_global_id()
    question = question_obj(id=question_number,
        category=category,
        question=question,
        answer1=answer1,
        answer2=answer2,
        answer3=answer3,
        answer4=answer4,
        answerid=answerid)
    question.key = ndb.Key(question_obj, question_number)
    question.put()

    return question_number
 
def getQuestion(id):
    return question_obj.query(question_obj.id == id)
 
def get_oldest_questions(num):
    query= question_obj.query()
    query.order(question_obj.create_datetime)
   
    return query.fetch(num)

def populate_db():
    txt = open('questions.txt')
    linesep = "\n"
    print("working")
    list = []

    for line in txt:
        list.append(line)

    for x in range(0,len(list), 6):
        question = list[x]
        answer1 = list[x+1]
        answer2 = list[x+2]
        answer3 = list[x+3]
        answer4 = list[x+4]
        answerid = list[x+5]
        create_question("Test", question, answer1, answer2, answer3,
            answer4, answerid)
