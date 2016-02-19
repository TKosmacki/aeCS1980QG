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

class ProfilePageHandler(webapp2.RequestHandler):
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
		render_template(self, 'profile.html', page_params)

	def post(self):
		id = get_user_id()
		name = self.request.get("name")
		location = self.request.get("location")
		interests = self.request.get("interests")

		models.update_profile(id, name, location, interests)

		self.redirect('/profile?id=' + id + "&search=" + get_user_email())

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
        review = models.getQuestion(id)
        page_params = {
          'user_email': get_user_email(),
          'login_url': users.create_login_url(),
          'logout_url': users.create_logout_url('/'),
          'review': review,
        }
        render_template(self, 'newQuestionReview.html', page_params)

#Brings up a table that displays information on the most recent 1000 questions
class ReviewNewQuestions(webapp2.RequestHandler):
    def get(self):
        #just loops and prints every question from query
        review = models.get_oldest_questions(1000)
        page_params = {
          'user_email': get_user_email(),
          'login_url': users.create_login_url(),
          'logout_url': users.create_logout_url('/'),
          'review': review,
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
    def get(self):
        questionList = []
        for x in range(10):
            questionList.append(models.getQuestion(str(x+1)))

        numCorrect = 0;
        currQ = questionList.pop()
        userAnswer10 = self.request.get('answer10')
        logging.warning('answer'+currQ.id)
        logging.warning(userAnswer10)
        if (userAnswer10 == currQ.answerid):
            numCorrect = numCorrect+1
        currQ = questionList.pop()
        userAnswer9 = self.request.get('answer9')
        if (userAnswer9 == currQ.answerid):
            numCorrect = numCorrect+1
        currQ = questionList.pop()
        userAnswer8 = self.request.get('answer8')
        if (userAnswer8 == currQ.answerid):
            numCorrect = numCorrect+1
        currQ = questionList.pop()
        userAnswer7 = self.request.get('answer7')
        if (userAnswer7 == currQ.answerid):
            numCorrect = numCorrect+1
        currQ = questionList.pop()
        userAnswer6 = self.request.get('answer6')
        if (userAnswer6 == currQ.answerid):
            numCorrect = numCorrect+1
        currQ = questionList.pop()
        userAnswer5 = self.request.get('answer5')
        if (userAnswer5 == currQ.answerid):
            numCorrect == numCorrect+1
        currQ = questionList.pop()
        userAnswer4 = self.request.get('answer4')
        if (userAnswer4 == currQ.answerid):
            numCorrect = numCorrect+1
        currQ = questionList.pop()
        userAnswer3 = self.request.get('answer3')
        logging.warning(userAnswer3)
        if (userAnswer3 == currQ.answerid):
            numCorrect = numCorrect+1
        currQ = questionList.pop()
        userAnswer2 = self.request.get('answer2')
        logging.warning(userAnswer2)
        if (userAnswer2 == currQ.answerid):
            numCorrect = numCorrect+1
        currQ = questionList.pop()
        userAnswer1 = self.request.get('answer1')
        logging.warning(userAnswer1)
        if (userAnswer1 == currQ.answerid):
            numCorrect = numCorrect+1


        page_params = {
          'user_email': get_user_email(),
          'login_url': users.create_login_url(),
          'logout_url': users.create_logout_url('/'),
          'numCorrect': numCorrect,
        }
        render_template(self,'quizResults.html',page_params)


#class checkAnswer(webapp2.RequestHandler):
#    def get(self):



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
  ('/submitQuiz',submitQuiz)
  #('/checkAnswer',checkAnswer),
]
app = webapp2.WSGIApplication(mappings, debug=True)
