import webapp2
import models
from google.appengine.ext import ndb

class validate_questions(webapp2.RequestHandler):
    def get(self):
        #just loops and prints every question from query
        review = models.get_oldest_questions(1000,False) #searches 1000 oldest invalid questions
        if review:
            for question in review:
                if question.score > 0:
                    question.accepted = True
                    question.up_voters = []
                    question.down_voters = []
                    question.put()
                
                if question.score < 1:
                    #figure out how to delete
                    return

mappings = [
  ('/tasks/validate_questions', validate_questions),
]

app = webapp2.WSGIApplication(mappings, debug=True)