import random
import logging
import os
import webapp2
import datetime
import time
from google.appengine.ext.webapp import template
from google.appengine.api import users
from google.appengine.ext import ndb
from google.appengine.api import memcache

#MODELS
###############################################################################
class User(ndb.Model):
    user_id = ndb.StringProperty()
    name = ndb.StringProperty(default="No Name")
    location = ndb.StringProperty(default="No Class")
    interests = ndb.StringProperty(default="No Interests")
    image_url = ndb.BlobKeyProperty()
    score = ndb.IntegerProperty(default=0) #maybe have a score variable for each category

class Answer(ndb.Model):
    questionKey = ndb.KeyProperty()
    chosenAnswer = ndb.StringProperty()
    category = ndb.StringProperty()
    create_datetime = ndb.DateTimeProperty(auto_now_add = True)
    correct = ndb.BooleanProperty()

class Question(ndb.Model):
    category = ndb.StringProperty()
    question = ndb.StringProperty()
    answer1 = ndb.StringProperty()
    answer2 = ndb.StringProperty()
    answer3 = ndb.StringProperty()
    answer4 = ndb.StringProperty()
    answerid = ndb.StringProperty()
    creator = ndb.StringProperty(default="user")
    correctAnswers = ndb.IntegerProperty(default=0)
    incorrectAnswers = ndb.IntegerProperty(default=0)
    answer1Selections = ndb.IntegerProperty(default=0)
    answer2Selections = ndb.IntegerProperty(default=0)
    answer3Selections = ndb.IntegerProperty(default=0)
    answer4Selections = ndb.IntegerProperty(default=0)
    totalAnswers = ndb.IntegerProperty(default=0)
    explanation = ndb.StringProperty(default="No Explanation Provided")
    create_datetime = ndb.DateTimeProperty(auto_now_add=True)
    accepted = ndb.BooleanProperty(default=False)
    up_voters = ndb.StringProperty(repeated=True)
    down_voters = ndb.StringProperty(repeated=True)
    score = ndb.IntegerProperty(default=0)
    image_urlQ = ndb.BlobKeyProperty()
    urlkey = ndb.StringProperty()

#CREATORS
###############################################################################
def createUser(id):
    profile = User()
    profile.user_id = id
    profile.key = ndb.Key(User,id)
    profile.put()

    memcache.set(id, profile, namespace="profile")

#adds an Answer object to the Datastore, as a child of User 'userid'
#updates Question with statistics
def createAnswer(userid, questionKey, chosenAnswer):
    answer = Answer(parent=ndb.Key(User, userid), )
    question = getQuestion(questionKey)

    answer.questionKey = questionKey
    answer.chosenAnswer = chosenAnswer
    answer.category = question.category

    rightAnswer = question.answerid
    if int(chosenAnswer) == int(rightAnswer):
        question.correctAnswers += 1
        answer.correct = True
    else:
        question.incorrectAnswers += 1
        answer.correct = False

    question.totalAnswers += 1

    if chosenAnswer == '1':
        question.answer1Selections += 1
    elif chosenAnswer == '2':
        question.answer2Selections += 1
    elif chosenAnswer == '3':
        question.answer3Selections += 1
    elif chosenAnswer == '4':
        question.answer4Selections += 1
    else:
        logging.critical("Answer isn't 1, 2, 3, or 4")


    question.put()
    answer.put()

#creates and stores question in database
def create_question(category,question,answer1,answer2,answer3,answer4,answerid,explanation,creator,valid,image_urlQ = None):
    question = Question(category=category,
        question=question,
        answer1=answer1,
        answer2=answer2,
        answer3=answer3,
        answer4=answer4,
        answerid=answerid,
        explanation=explanation,
        creator=creator,
        accepted=valid,
        image_urlQ=image_urlQ,)
    logging.warning(question.key)
    question.put()

    logging.warning(question.key.urlsafe())
    question.urlkey = question.key.urlsafe()
    question.put()
    return question.key

#MODIFIERS
###############################################################################
def update_profile(id, name, location, interests, image_url = None):
    profile = get_User(id)
    profile.populate(name = name, location = location, interests = interests, image_url = image_url)
    profile.put()
    memcache.set(id, profile, namespace="profile")

#increments the vote counter
def addVote(id,email):
    question = ndb.Key(Question,id).get()

    if not check_if_up_voted(question.up_voters, email):
        question.up_voters.append(email)
        if check_if_down_voted(question.down_voters, email):
            question.down_voters.remove(email)

        question.score = len(question.up_voters) - len(question.down_voters)
        if question.score < 0:
            question.score = 0
        question.put()

def decVote(id,email):
    question = ndb.Key(Question,id).get()

    if not check_if_down_voted(question.down_voters, email):
        question.down_voters.append(email)
        if check_if_up_voted(question.up_voters, email):
            question.up_voters.remove(email)

        question.score = len(question.up_voters) - len(question.down_voters)
        if question.score < 0:
            question.score = 0
        question.put()

#GETTERS
###############################################################################
def check_if_user_exists(id):
    result = list()
    q = User.query(User.user_id == id)
    q = q.fetch(1)
    return q

#returns an iterable query object that has all answers of userid
def get_user_answers(userKey):
    answers = Answer.query(ancestor=ndb.Key(User, userKey)).fetch()
    return answers

#returns an iterable query object that has all answers of category
def get_category_answers(inCategory):
    answers = Answer.query(Answer.category == inCategory)
    return answers

def get_User(id):
    result = memcache.get(id, namespace="profile")
    if not result:
        result = ndb.Key(User, id).get()
        memcache.set(id, result, namespace="profile")
    return result

def get_image(image_id):
  return ndb.Key(urlsafe=image_id).get()

def getQuestion(key):
    ac_obj = key.get()
    return ac_obj

def getQuestionFromURL(key):
    logging.warning(key)
    key = ndb.Key(urlsafe=key)
    return key.get()

def getQuestionsCat(category,number):
    q = Question.query(Question.category == category)
    #still need to random
    questions = list()
    for i in q.fetch(number):
        questions.append(i)
    return questions

def check_if_up_voted(has_up_voted,email):
    if email in has_up_voted:
        return True
    return False

def check_if_down_voted(has_down_voted, email):
    if email in has_down_voted:
        return True
    return False

#return: (list) of questions, oldest first
def get_oldest_questions(num,val):
    if val: #searches for valid questions for reviewal
        query= Question.query(Question.accepted == True)
        query.order(Question.create_datetime)
    else: #search for invalid questions
        query= Question.query(Question.accepted == False)
        query.order(Question.create_datetime)

    return query.fetch(num)

#UTILITY
###############################################################################

#fills database with Questions from questions.txt
def populateQuestions():
    txt = open('questions.txt')
    list = []

    for line in txt:
        list.append(line)

    for x in range(0,len(list)/2, 6):
        question = list[x]
        answer1 = list[x+1]
        answer2 = list[x+2]
        answer3 = list[x+3]
        answer4 = list[x+4]
        answerid = list[x+5]
        create_question("Test", question, answer1, answer2, answer3,
            answer4, answerid,"None","Stephen Curry",True)

    for x in range((len(list)/2), len(list), 6):
        question = list[x]
        answer1 = list[x+1]
        answer2 = list[x+2]
        answer3 = list[x+3]
        answer4 = list[x+4]
        answerid = list[x+5]
        create_question("Test2", question, answer1, answer2, answer3,
            answer4, answerid,"None","Stephen Curry",True)

#creates one Answer per Question per User
def populateAnswers():
    users = User.query().fetch(10)
    for user in users:
        questions = Question.query()
        for question in questions:
            createAnswer(user.user_id, question.key, str(random.randint(1,4)))


