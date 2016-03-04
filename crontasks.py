import webapp2
import models
from google.appengine.ext import ndb

class validate_questions(webapp2.RequestHandler):
    #just loops and prints every question from query
    review = models.get_oldest_questions(1000,False) #searches 1000 oldest invalid questions
    if review:
        for question_obj in review:
            if question_obj.score > 0:
                question_obj.accepted = True
                question_obj.put()
                
mappings = [
    ('/tasks/validate_questions', validate_questions),
]

app = webapp2.WSGIApplication(mappings, debug=True)