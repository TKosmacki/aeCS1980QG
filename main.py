import logging
import os
import webapp2
import models
import time
import json

from google.appengine.api import images
from google.appengine.api import mail
from google.appengine.api import users
from google.appengine.ext import ndb
from google.appengine.ext import blobstore
from google.appengine.ext.webapp import template
from google.appengine.api import mail
from google.appengine.ext.webapp import blobstore_handlers

run=False

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
        is_admin = 0
        if users.is_current_user_admin():
            is_admin = 1
        q = models.check_if_user_exists(id)
	page_params = {
        'user_email': get_user_email(),
        'login_url': users.create_login_url('/firstLogin'),
        'logout_url': users.create_logout_url('/'),
        'user_id': id,
        'admin' : is_admin
        }
        render_template(self, 'index.html', page_params)

class LoginPageHandler(webapp2.RequestHandler):
    def get(self):
        id = get_user_id()
        user = models.get_User(id)
        if user is None:
            self.redirect('/profile?id=' + id)
        else:
            self.redirect('/')

class SubmitPageHandler(webapp2.RequestHandler):
    def get(self):
        id = get_user_id()
        is_admin = 0
        if users.is_current_user_admin():
            is_admin = 1
        q = models.check_if_user_exists(id)

        page_params = {
            'upload_urlQ': blobstore.create_upload_url('/NewQuestion'),
            'user_email': get_user_email(),
            'login_url': users.create_login_url(),
            'logout_url': users.create_logout_url('/'),
            'user_id': id,
            'admin' : is_admin
        }
        render_template(self, 'newQuestionSubmit.html', page_params)

class NewQuestion(blobstore_handlers.BlobstoreUploadHandler):
    def post(self):
        id = get_user_id()
        q = models.get_User(id)
        creator = q.name
        explanation = self.request.get('explanation')
        if not explanation:
            explanation = "No Explanation Provided"
        category = self.request.get('category')
        question = self.request.get('questiontext')
        answer1 = self.request.get('answer1')
        answer2 = self.request.get('answer2')
        answer3 = self.request.get('answer3')
        answer4 = self.request.get('answer4')
        answerid = self.request.get('answerid')
        try:
            upload_files = self.get_uploads()
            blob_info = upload_files[0]
            type = blob_info.content_type

            # if the uploaded file is an image
            if type in ['image/jpeg', 'image/png', 'image/gif', 'image/webp']:
                image = blob_info.key()
                questionID = models.create_question(category,
                        question,answer1,answer2,answer3,answer4,answerid,
                        explanation,creator,False,image)

            # if the uploaded file is not an image
            else:
                questionID = models.create_question(category,
                        question,answer1,answer2,answer3,answer4,answerid,
                        explanation,creator,False)

            self.redirect('/NewQuestion?id=' + questionID.urlsafe())

        # no image to upload
        except IndexError:
            questionID = models.create_question(category,
                    question,answer1,answer2,answer3,answer4,answerid,
                    explanation,creator,False)

        self.redirect('/NewQuestion?id=' + questionID.urlsafe())

    def get(self):
        id = self.request.get('id')
        page_params = {
            'questionID' : id
        }
        render_template(self, 'confirmationPage.html', page_params)

class ReviewSingleQuestion(webapp2.RequestHandler):
    def get(self):
        id = self.request.get('id')
        uID = get_user_id()
        logging.warning(id)
        review = models.getQuestionFromURL(id)
        is_admin = 0
        if users.is_current_user_admin():
            is_admin = 1
        page_params = {
        'user_email': get_user_email(),
        'login_url': users.create_login_url(),
        'logout_url': users.create_logout_url('/'),
        'user_id': uID,
        'review': review,
        'admin' : is_admin
        }
        render_template(self, 'newQuestionReview.html', page_params)

#Brings up a table that displays information on the most recent 1000 questions
class ReviewNewQuestions(webapp2.RequestHandler):
    def get(self):
        uID = get_user_id()
        #just loops and prints every question from query
        review = models.get_oldest_questions(1000,False) #searches 1000 oldest invalid questions
        is_admin = 0
        if users.is_current_user_admin():
            is_admin = 1
        page_params = {
        'user_email': get_user_email(),
        'login_url': users.create_login_url(),
        'logout_url': users.create_logout_url('/'),
        'user_id': uID,
        'review': review,
        'admin' : is_admin
        }
        render_template(self, 'reviewQuestions.html', page_params)

#Brings up a table that displays information on the most recent 1000 questions
class ReviewOldQuestions(webapp2.RequestHandler):
    def get(self):
        uID = get_user_id()
        #just loops and prints every question from query
        review = models.get_oldest_questions(1000,True) #searches 1000 oldest valid questions
        is_admin = 0
        if users.is_current_user_admin():
            is_admin = 1
        page_params = {
            'user_email': get_user_email(),
            'login_url': users.create_login_url(),
            'logout_url': users.create_logout_url('/'),
            'user_id': uID,
            'review': review,
            'admin' : is_admin
        }
        render_template(self, 'reviewQuestionsValid.html', page_params)

class test(webapp2.RequestHandler):
    def get(self):
        #if not users.is_current_user_admin(): #stops from running this if user is not admin
        #    self.redirect("/")
        #    return
        #global run
        #if run==True: #stops from running more than once
        #    self.redirect("/")
        #    return
        #run=True
        models.populateQuestions()
        models.populateAnswers()
       # models.createAnswer(get_user_id(),'1','2')
        id = get_user_id()
        is_admin = 0
        if users.is_current_user_admin():
            is_admin = 1
        q = models.check_if_user_exists(id)
        page_params = {
        'user_email': get_user_email(),
        'login_url': users.create_login_url(),
        'logout_url': users.create_logout_url('/'),
        'user_id': id,
        'admin' : is_admin
        }
        render_template(self, 'index.html', page_params)

class AnswerQuestion(webapp2.RequestHandler):
    def get(self):
        #answerid = self.request.get('answerid')
        #id = self.request.get('id')
        review = models.get_oldest_questions(1)
        is_admin = 0
        if users.is_current_user_admin():
            is_admin = 1
        page_params = {
            'user_email': get_user_email(),
            'login_url': users.create_login_url(),
            'logout_url': users.create_logout_url('/'),
            'review': review,
            'admin': is_admin,
        }
        render_template(self, 'answerQuestion.html',page_params)

class ProfileHandler(blobstore_handlers.BlobstoreUploadHandler):
    def get(self):
        if not get_user_email(): #stops from creating a profile if not logged in
            self.redirect("/")
            return
        id = self.request.get("id")
        q = models.check_if_user_exists(id)
        if q == []:
            models.createUser(id)
        is_admin = 0
        if users.is_current_user_admin():
            is_admin = 1
        page_params = {
            'upload_url': blobstore.create_upload_url('/profile'),
            'user_email': get_user_email(),
            'login_url': users.create_login_url(),
            'logout_url': users.create_logout_url('/'),
            'user_id': get_user_id(),
            'profile': models.get_User(id),
            'admin': is_admin,
        }
        render_template(self, 'profile.html', page_params)

    def post(self):
        #try to upload an image
        try:
            upload_files = self.get_uploads()
            blob_info = upload_files[0]
            type = blob_info.content_type
            id = get_user_id()
            name = self.request.get("name")
            year = self.request.get("year")
            interests = self.request.get("interests")
            employer = self.request.get("employer")
            bio = self.request.get("bio")

            # if the uploaded file is an image
            if type in ['image/jpeg', 'image/png', 'image/gif', 'image/webp']:
                image = blob_info.key()
                models.update_profile(id, name, year, interests, bio, employer, image)

            # if the uploaded file is not an image
            else:
                models.update_profile(id, name, year, interests, bio, employer)

            self.redirect('/profile?id=' + id)
        # no image to upload
        except IndexError:
            id = get_user_id()
            name = self.request.get("name")
            year = self.request.get("year")
            interests = self.request.get("interests")
            employer = self.request.get("employer")
            bio = self.request.get("bio")
            models.update_profile(id, name, year, interests, bio, employer)

        self.redirect('/profile?id=' + id)

class ImageHandler(blobstore_handlers.BlobstoreDownloadHandler):
  def get(self):
    id = self.request.get("id")
    profile = models.get_User(id)
    try:
     image = images.Image(blob_key=profile.image_url)
     self.send_blob(profile.image_url)
    except Exception:
     pass

class ImageHandlerQuestion(blobstore_handlers.BlobstoreDownloadHandler):
  def get(self):
    urlkey = self.request.get('urlkey')
    review = models.getQuestionFromURL(urlkey)
    try:
     image = images.Image(blob_key=review.image_urlQ)
     self.send_blob(review.image_urlQ)
    except Exception:
     pass

class submitQuiz(webapp2.RequestHandler):
    def post(self):
        is_admin = 0
        if users.is_current_user_admin():
            is_admin = 1
        page_params = {
            'user_email': get_user_email(),
            'login_url': users.create_login_url(),
            'logout_url': users.create_logout_url('/'),
            'correctCount': numCorrect,
            'totalCount': numTotal,
            'question_obj': argQ,
            'admin': is_admin,
        }
        render_template(self,'quizResults.html',page_params)

class answerSingle(webapp2.RequestHandler):
    def post(self):
        self.response.headers.add_header('Access-Control-Allow-Origin', '*')
        self.response.headers['Content-Type'] = 'application/json'
        logging.warning("WHAT UP")
        logging.warning(self.request.get('userID'))
        logging.warning(self.request.get('qKey'))
        logging.warning(self.request.get('userSelection'))
        data = self.request.get('data')

        logging.warning(data)
        #obj = json.loads(data)
        #logging.warning(obj[userSelection])
        #createAnswer(obj['userID'],obj['qKey'],obj[userSelection])

class submitAnswer(webapp2.RequestHandler):
    def post(self):
        id = self.request.get('hidden_questionid')
        question = models.getQuestion(id)
        if not question: #checks to make sure a question was actually fetched
            #maybe redirect here instead of showing an empty question page, error page possibly
            self.redirect('home')
            logging.warning("no question found with that id")
        answerid = question.answerid
        questionid = self.request.get('userAnswer')
        correctCount = self.request.get('hidden_correctCount')
        totalCount = self.request.get('hidden_totalCount')
        answerid = int(answerid)
        questionid = int(questionid)
        correctCount = int(correctCount)
        totalCount = int(totalCount)
        id = get_user_id()
        is_admin = 0
        if users.is_current_user_admin():
            is_admin = 1
        if (questionid == answerid):
            correctCount = correctCount+1
        totalCount = totalCount+1
        if (totalCount == 10):
            page_params = {
                'user_email': get_user_email(),
                'login_url': users.create_login_url(),
                'logout_url': users.create_logout_url('/'),
                'correctCount': correctCount,
                'totalCount': totalCount,
                'admin': is_admin,
            }
            render_template(self,'quizResults.html',page_params)
            return
        argQ = models.getQuestion(str(2+totalCount))
        page_params = {
            'user_email': get_user_email(),
            'login_url': users.create_login_url(),
            'logout_url': users.create_logout_url('/'),
            'correctCount': correctCount,
            'totalCount': totalCount,
            'question_obj': argQ,
            'user_id':id,
            'admin': is_admin,
        }
        render_template(self,'answerSingle.html',page_params)


def obj_dict(obj):
    return obj.__dict__


class categoryQuiz(webapp2.RequestHandler):
    def get(self):
        is_admin = 0
        if users.is_current_user_admin():
            is_admin = 1
        #category = self.request.get('category')
        number = self.request.get('number')
        category = "Test"
        number = 7
        questions = models.getQuestionsCat(category,number)

        #for i in questions:
        #    self.response.out.write(json.dumps(i.to_dict(exclude=['category','creator','accepted','up_voted','down_voted','create_datetime']))+"</br></br>")


        qList = []
        for q in questions:
            temp = q.to_dict(exclude=['image_urlQ','category','creator','accepted','up_voters','down_voters','create_datetime'])
            qList.append(temp)

        jList = json.dumps(qList, default=obj_dict)
        #jList = json.dumps([temp.__dict__ for temp in qList])
        #self.response.out.write("</br></br></br>")
        #self.response.out.write(qList)
        page_params = {
              'userid': get_user_id(),
              'num':number,
              'question_list' : jList,
              'user_email': get_user_email(),
              'login_url': users.create_login_url(),
              'logout_url': users.create_logout_url('/'),
			  'admin': is_admin,
            }
        render_template(self, 'answerQuestionsCat.html', page_params)

#used for reporting a question from the review question page
class reportHandler(webapp2.RequestHandler):
    def post(self):
        body = "Comment:\n" + self.request.get("comment")
        sender_address = get_user_email() #not sure if we want to do this
        question = self.request.get("id")
        body = body + "\n\nVisit the question here: aecs1980qg.appspot.com/ReviewQuestion?id=" + question
        subject = "A question has been reported"
        mail.send_mail(sender_address , "bogdanbg24@gmail.com" , subject, body)
        self.redirect("/ReviewNewQuestions")

#used for reporting a question in the quiz
class reportQuizHandler(webapp2.RequestHandler):
    def post(self):
        body = "Comment:\n" + self.request.get("comment")
        sender_address = get_user_email() #not sure if we want to do this
        question = self.request.get("id")
        body = body + "\n\nVisit the question here: aecs1980qg.appspot.com/ReviewQuestion?id=" + question
        subject = "A question has been reported"
        mail.send_mail(sender_address , "bogdanbg24@gmail.com" , subject, body)

class addVote(webapp2.RequestHandler):
    def post(self):
        id = self.request.get("id")
        email = get_user_email()
        models.addVote(id,email)
        time.sleep(1)
        self.redirect("/ReviewNewQuestions") #maybe want a confirmation page

class decVote(webapp2.RequestHandler):
    def post(self):
        id = self.request.get("id")
        email = get_user_email()
        models.decVote(id,email)
        time.sleep(1)
        self.redirect("/ReviewNewQuestions")

###############################################################################
mappings = [
  ('/', MainPageHandler),
  ('/profile', ProfileHandler),
  ('/submitNew', SubmitPageHandler),
  ('/NewQuestion', NewQuestion),
  ('/ReviewQuestion', ReviewSingleQuestion),
  ('/meanstackakalamestack', test),
  ('/ReviewNewQuestions', ReviewNewQuestions),
  ('/ReviewOldQuestions', ReviewOldQuestions),
  ('/AnswerQuestion', AnswerQuestion),
  ('/submitQuiz',submitQuiz),
  ('/answerSingle',answerSingle),
  ('/submitAnswer',submitAnswer),
  ('/report', reportHandler),
  ('/reportQuiz', reportQuizHandler),
  ('/incrementVote' , addVote),
  ('/image', ImageHandler),
  ('/imageQ', ImageHandlerQuestion),
  ('/decrementVote', decVote),
  ('/takeQuiz', categoryQuiz),
  ('/firstLogin', LoginPageHandler)
]
app = webapp2.WSGIApplication(mappings, debug=True)
