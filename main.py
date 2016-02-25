import logging
import os
import webapp2
import models

from google.appengine.api import mail
from google.appengine.api import users
from google.appengine.ext import ndb
from google.appengine.ext.webapp import template

###############################################################################
# We'll just use this convenience function to retrieve and render a template.
def render_template(handler, templatename, templatevalues={}):
  path = os.path.join(os.path.dirname(__file__), 'templates/' + templatename)
  html = template.render(path, templatevalues)
  handler.response.out.write(html)


###############################################################################
def get_user_email():
  result = None
  user = users.get_current_user()
  if user:
    result = user.email()
  return result

def get_user_id():
	result = None
	user = users.get_current_user()
	if user:
		result = user.user_id()
	return result

class MainPageHandler(webapp2.RequestHandler):
	def get(self):
		id = get_user_id()

		q = models.check_if_user_profile_exists(id)

		page_params = {
		'user_email': get_user_email(),
		'login_url': users.create_login_url(),
		'logout_url': users.create_logout_url('/'),
		'user_id': id,
		}
		render_template(self, 'index.html', page_params)


class SubmitPageHandler(webapp2.RequestHandler):
	def get(self):
		id = get_user_id()

		q = models.check_if_user_profile_exists(id)

		page_params = {
		'user_email': get_user_email(),
		'login_url': users.create_login_url(),
		'logout_url': users.create_logout_url('/'),
		'user_id': id,
		}
		render_template(self, 'newQuestionSubmit.html', page_params)

class NewQuestion(webapp2.RequestHandler):
    def post(self):
        email = get_user_email()
        category = self.request.get('category')
        question = self.request.get('questiontext')
        answer1 = self.request.get('answer1')
        answer2 = self.request.get('answer2')
        answer3 = self.request.get('answer3')
        answer4 = self.request.get('answer4')
        answerid = self.request.get('answerid')
        questionID = models.create_question(category,question,answer1,answer2,answer3,answer4,answerid,email)
        self.redirect('/NewQuestion?id=' + questionID)

    def get(self):
        id = self.request.get('id')
        page_params = {
            'questionID' : id
        }
        render_template(self, 'confirmationPage.html', page_params)

class ReviewQuestion(webapp2.RequestHandler):
    def get(self):
        id = self.request.get('id')
        uID = get_user_id()
        review = models.getQuestion(id)
        page_params = {
          'user_email': get_user_email(),
          'login_url': users.create_login_url(),
          'logout_url': users.create_logout_url('/'),
          'review': review,
          'user_id' : uID,
        }
        render_template(self, 'newQuestionReview.html', page_params)

#Brings up a table that displays information on the most recent 1000 questions
class ReviewNewQuestions(webapp2.RequestHandler):
    def get(self):
        uID = get_user_id()
        #just loops and prints every question from query
        review = models.get_oldest_questions(1000)
        page_params = {
          'user_email': get_user_email(),
          'login_url': users.create_login_url(),
          'logout_url': users.create_logout_url('/'),
          'review': review,
          'user_id' : uID,
        }
        render_template(self, 'reviewQuestions.html', page_params)

class test(webapp2.RequestHandler):
	def get(self):
		models.create_global_id()
		models.populate_db()
		page_params = {
		'user_email': get_user_email(),
		'login_url': users.create_login_url(),
		'logout_url': users.create_logout_url('/'),
		'user_id': get_user_id(),
		}
		render_template(self, 'blanktest.html', page_params)

class AnswerQuestion(webapp2.RequestHandler):
    def get(self):
        #answerid = self.request.get('answerid')
        #id = self.request.get('id')
        review = models.get_oldest_questions(1)
        page_params = {
          'user_email': get_user_email(),
          'login_url': users.create_login_url(),
          'logout_url': users.create_logout_url('/'),
          'review': review,
        }
        render_template(self, 'answerQuestion.html',page_params)

class ProfileHandler(webapp2.RequestHandler):
	def get(self):
		id = self.request.get("id")
		logging.warning(id)
		q = models.check_if_user_profile_exists(id)
		if q == []:
			models.create_profile(id)

		page_params = {
			'user_email': get_user_email(),
			'login_url': users.create_login_url(),
			'logout_url': users.create_logout_url('/'),
			'user_id': get_user_id(),
			'profile': models.get_user_profile(id),
		}
		render_template(self, 'profile1.html', page_params)

	def post(self):
		id = get_user_id()
		name = self.request.get("name")
		location = self.request.get("location")
		interests = self.request.get("interests")

		models.update_profile(id, name, location, interests)

		self.redirect('/profile?id=' + id + "&search=" + get_user_email())

class RunGame(webapp2.RequestHandler):
    def get(self):
        questionList = []
        for x in range(10):
            questionList.append(models.getQuestion(str(x+1)))

        page_params = {
          'user_email': get_user_email(),
          'login_url': users.create_login_url(),
          'logout_url': users.create_logout_url('/'),
          'questionList': questionList,
        }
        render_template(self, 'answerQuestion.html',page_params)

class submitQuiz(webapp2.RequestHandler):
    def post(self):
        page_params = {
          'user_email': get_user_email(),
          'login_url': users.create_login_url(),
          'logout_url': users.create_logout_url('/'),
          'correctCount': numCorrect,
          'totalCount': numTotal,
          'question_obj': argQ,
        }
        render_template(self,'quizResults.html',page_params)


class answerSingle(webapp2.RequestHandler):
    def get(self):
        argQ = models.getQuestion(str(2))
        numCorrect = 0
        numTotal = 0
        page_params = {
          'user_email': get_user_email(),
          'login_url': users.create_login_url(),
          'logout_url': users.create_logout_url('/'),
          'correctCount': numCorrect,
          'totalCount': numTotal,
          'question_obj': argQ,
        }
        render_template(self,'answerSingle.html',page_params)

class submitAnswer(webapp2.RequestHandler):
    def post(self):
        answerid = self.request.get('hidden_answerid')
        questionid = self.request.get('userAnswer')
        correctCount = self.request.get('hidden_correctCount')
        totalCount = self.request.get('hidden_totalCount')
        answerid = int(answerid)
        questionid = int(questionid)
        correctCount = int(correctCount)
        totalCount = int(totalCount)
        if (totalCount == 5):
            page_params = {
              'user_email': get_user_email(),
              'login_url': users.create_login_url(),
              'logout_url': users.create_logout_url('/'),
              'correctCount': correctCount,
              'totalCount': totalCount,
            }
            render_template(self,'quizResults.html',page_params)

        if (totalCount == 10):
            page_params = {
              'user_email': get_user_email(),
              'login_url': users.create_login_url(),
              'logout_url': users.create_logout_url('/'),
              'correctCount': correctCount,
              'totalCount': totalCount,
            }
            render_template(self,'quizResults.html',page_params)
            return
        if (questionid == answerid):
            correctCount = correctCount+1
        totalCount = totalCount+1
        argQ = models.getQuestion(str(2+totalCount))
        page_params = {
          'user_email': get_user_email(),
          'login_url': users.create_login_url(),
          'logout_url': users.create_logout_url('/'),
          'correctCount': correctCount,
          'totalCount': totalCount,
          'question_obj': argQ,
        }
        render_template(self,'answerSingle.html',page_params)



###############################################################################
mappings = [
  ('/', MainPageHandler),
  ('/profile', ProfileHandler),
  ('/submitNew', SubmitPageHandler),
  ('/NewQuestion', NewQuestion),
  ('/ReviewQuestion', ReviewQuestion),
  ('/meanstackakalamestack', test),
  ('/ReviewNewQuestions', ReviewNewQuestions),
  ('/AnswerQuestion', AnswerQuestion),
  ('/RunGame', RunGame),
  ('/submitQuiz',submitQuiz),
  ('/answerSingle',answerSingle),
  ('/submitAnswer',submitAnswer)
]
app = webapp2.WSGIApplication(mappings, debug=True)
