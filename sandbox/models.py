import webapp2
from google.appengine.ext import ndb
from google.appengine.api import memcache

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

class global_id(ndb.Model):
    next_id = ndb.IntegerProperty()

    def increase_id(self):
        self.next_id = self.next_id + 1

def create_global_id():
    id = ndb.Key(global_id, "number").get()
    #logging.warning(id)
    if id == None:
        id = global_id()
        id.next_id = 1
        id.key = ndb.Key(global_id, "number")
        id.put()
        memcache.set("number", id, namespace="global_id")

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

def get_oldest_questions():
    query= question_obj.query()
    query.order(question_obj.create_datetime)
   
    #returns list of 20 questions, or fewer if there are none left 
    return query.fetch(20)
