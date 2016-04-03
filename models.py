import json
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
    name = ndb.StringProperty()
    year = ndb.StringProperty()
    interests = ndb.StringProperty()
    employer = ndb.StringProperty(default="University of Pittsburgh")
    bio = ndb.StringProperty()
    image_url = ndb.BlobKeyProperty()

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
    create_date = ndb.DateProperty(auto_now_add=True)
    accepted = ndb.BooleanProperty(default=False)
    up_voters = ndb.StringProperty(repeated=True)
    down_voters = ndb.StringProperty(repeated=True)
    up_votes = ndb.IntegerProperty(default = 0)
    down_votes = ndb.IntegerProperty(default = 0)
    rating = ndb.ComputedProperty(lambda self:  self.up_votes - self.down_votes)
    score = ndb.IntegerProperty(default=0)
    image_urlQ = ndb.BlobKeyProperty()
    urlkey = ndb.StringProperty()

class Score(ndb.Model):
    category = ndb.StringProperty()
    score = ndb.IntegerProperty()
    day = ndb.StringProperty()
    month = ndb.StringProperty()
    year = ndb.StringProperty()

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
#updates Score object per category
def createAnswer(userid, questionKey, chosenAnswer, points = 0):
    answer = Answer(parent=ndb.Key(User, userid), )
    question = getQuestion(questionKey)

    scoreList = Score.query(Score.category == question.category, ancestor = ndb.Key(User, userid)).fetch(1)


    answer.questionKey = questionKey
    answer.chosenAnswer = chosenAnswer
    answer.category = question.category

    correctFlag = False

    rightAnswer = question.answerid
    if int(chosenAnswer) == int(rightAnswer):
        question.correctAnswers += 1
        answer.correct = True
        correctFlag = True
    else:
        question.incorrectAnswers += 1
        answer.correct = False
        correctFlag = False

    #Score hasn't been created
    if len(scoreList) == 0:
        if correctFlag == True:
            createScore(userid, question.category, points)
        else:
            createScore(userid, question.category, 0)
    else:
        if correctFlag:
            updateScore(userid, question.category, points)

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

def createScore(userid, category, points):
    scoreObj = Score(parent=ndb.Key(User, userid))
    scoreObj.category = category
    scoreObj.score = points
    scoreObj.put()


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
    question.put()

    #logging.warning(question.key.urlsafe())
    question.urlkey = question.key.urlsafe()
    question.put()
    return question.key


    
#MODIFIERS
###############################################################################
def update_profile(id, name, year, interests, bio, employer, image_url = None):
    profile = get_User(id)
    profile.populate(name = name, year = year, interests = interests, bio = bio, employer = employer, image_url = image_url)
    profile.put()
    memcache.set(id, profile, namespace="profile")
    
def updateQuestion(urlkey,category,questionIn,answer1,answer2,answer3,answer4,answerid,explanation,creator,valid,image_urlQ = None):
    questKey=ndb.Key(urlsafe=urlkey)
    question = questKey.get()
    question.category=category
    question.question=questionIn
    question.answer1=answer1
    question.answer2=answer2
    question.answer3=answer3
    question.answer4=answer4
    question.answerid=answerid
    question.explanation=explanation
    question.creator=creator
    question.accepted=valid
    question.image_urlQ=image_urlQ
    question.put()

def updateScore(userid, category, points):
    scoreList = Score.query(Score.category == category, ancestor = ndb.Key(User,
        userid)).fetch(1)
    scoreObj = scoreList[0]
    scoreObj.score = scoreObj.score + points
    scoreObj.put()

#increments the vote counter
def addVote(id,email):
    question = getQuestionFromURL(id)

    if not check_if_up_voted(question.up_voters, email):
        question.up_voters.append(email)
        question.up_votes+=1
        if check_if_down_voted(question.down_voters, email):
            question.down_voters.remove(email)
            question.down_votes-=1
        question.put()
        return True
        
    return False
def decVote(id,email):
    question = getQuestionFromURL(id)

    if not check_if_down_voted(question.down_voters, email):
        question.down_voters.append(email)
        question.down_votes+=1
        if check_if_up_voted(question.up_voters, email):
            question.up_voters.remove(email)
            question.up_votes-=1
        question.put()
        return True
        
    return False

def delete_question(key):
    getQuestion(key).delete()
    return

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
    query =  User.query(User.user_id == id).fetch(1)
    if len(query) == 0:
        return None
    return query[0]
    #result = memcache.get(id, namespace="profile")
    #if not result:
    #    result = ndb.Key(User, id).get()
    #    memcache.set(id, result, namespace="profile")
    #return result

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
    q = Question.query(Question.category == category, Question.accepted ==
            True).fetch()
    if len(q) == 0:
        logging.warning("There aren't any questions. Have you populated the database?")
        return None
    questions = list()
    for i in q.fetch():
        questions.append(i)
    random.shuffle(questions)
    results = list()
    for i in range(0,number):
        results.append(questions[i]) 
    return results

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
        query.order(Question.create_date)
    else: #search for invalid questions
        query= Question.query(Question.accepted == False)
        query.order(Question.create_date)

    return query.fetch(num)

#returns JSON list of {category, score} for a given user
def getCatUserScore(userid):
    user = get_User(userid)
    scores = Score.query(ancestor = ndb.Key(User, userid))
    scoreList = []
    for score in scores:
        temp = score.to_dict(include=['category', 'score'])
        scoreList.append(temp)
    jsonList = json.dumps(scoreList, default = obj_dict)
    logging.warning("JSON: "+jsonList)
    return jsonList

def getAllUserScores():
    users = User.query()
    scoreList = dict()
    for user in users:
        scores = Score.query(ancestor = ndb.Key(User, user.user_id))
        counter = 0
        for score in scores:
            counter += score.score
        scoreList[user.name] = counter
    jsonList = json.dumps(scoreList, default = obj_dict)
    logging.warning("JSON: "+jsonList)
    return jsonList


     

#UTILITY
###############################################################################

#fills database with Questions from questions.txt
def populateQuestions():
    txt = open('questions.txt')
    list = []

    for line in txt:
        list.append(line.rstrip())
    for x in range(0,60,6):
            question = list[x]
            answer1 = list[x+1]
            answer2 = list[x+2]
            answer3 = list[x+3]
            answer4 = list[x+4]
            answerid = list[x+5]
            create_question("PHARM 2001", question, answer1, answer2, answer3,
            answer4, answerid,"None","Stephen Curry",True)        
    for x in range(60,120, 6):
            question = list[x]
            answer1 = list[x+1]
            answer2 = list[x+2]
            answer3 = list[x+3]
            answer4 = list[x+4]
            answerid = list[x+5]
            create_question("PHARM 3023", question, answer1, answer2, answer3,
            answer4, answerid,"None","Stephen Curry",True)

    for x in range(120,180, 6):
            question = list[x]
            answer1 = list[x+1]
            answer2 = list[x+2]
            answer3 = list[x+3]
            answer4 = list[x+4]
            answerid = list[x+5]
            create_question("PHARM 3028", question, answer1, answer2, answer3,
            answer4, answerid,"None","Stephen Curry",True)
    for x in range(180,240, 6):
            question = list[x]
            answer1 = list[x+1]
            answer2 = list[x+2]
            answer3 = list[x+3]
            answer4 = list[x+4]
            answerid = list[x+5]
            create_question("PHARM 3040", question, answer1, answer2, answer3,
            answer4, answerid,"None","Stephen Curry",True)
    for x in range(240,300, 6):
            question = list[x]
            answer1 = list[x+1]
            answer2 = list[x+2]
            answer3 = list[x+3]
            answer4 = list[x+4]
            answerid = list[x+5]
            create_question("PHARM 5218", question, answer1, answer2, answer3,
            answer4, answerid,"None","Stephen Curry",True)

#creates one Answer per Question per User
def populateAnswers():
    users = User.query().fetch(10)
    for user in users:
        questions = Question.query()
        for question in questions:
            createAnswer(user.user_id, question.key, str(random.randint(1,4)), 10)


def obj_dict(obj):
    return obj.__dict__
