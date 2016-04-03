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

#Used for reviewing a single question, whether from the tables or from email
class ReviewSingleQuestion(blobstore_handlers.BlobstoreUploadHandler):
    def get(self):
        id = self.request.get('id')
        uID = get_user_id()
        logging.warning(id)
        review = models.getQuestionFromURL(id)
        is_admin = 0
        if users.is_current_user_admin():
            is_admin = 1
        page_params = {
            'upload_urlQE': blobstore.create_upload_url('/ReviewQuestion?id=' + id),
            'user_email': get_user_email(),
            'login_url': users.create_login_url(),
            'logout_url': users.create_logout_url('/'),
            'user_id': uID,
            'review': review,
            'admin' : is_admin
        }
        render_template(self, 'questionReview.html', page_params)
    def post(self):
        #try to upload an image
        try:
            upload_files = self.get_uploads()
            blob_info = upload_files[0]
            type = blob_info.content_type
            id = self.request.get('id')
            explanation = models.getQuestionFromURL(id).explanation
            if not explanation:
                explanation = "No Explanation Provided"
            category = models.getQuestionFromURL(id).category
            creator = models.getQuestionFromURL(id).creator
            questionIn = self.request.get('questiontext')
            answer1 = self.request.get('answer1')
            answer2 = self.request.get('answer2')
            answer3 = self.request.get('answer3')
            answer4 = self.request.get('answer4')
            answerid = self.request.get('answerid')
            logging.warning(category)
            logging.warning(creator)
            logging.warning(questionIn)
            logging.warning(answer1)
            logging.warning(answer2)
            logging.warning(answer3)
            logging.warning(answer4)
            logging.warning('Signed by anonymous user')
                # if the uploaded file is an image
            if type in ['image/jpeg', 'image/png', 'image/gif', 'image/webp']:
                image = blob_info.key()
                models.updateQuestion(id,category,questionIn,answer1,answer2,answer3,answer4,answerid,explanation,creator,True,image)

                # if the uploaded file is not an image
            else:
                models.updateQuestion(id,category,questionIn,answer1,answer2,answer3,answer4,answerid,explanation,creator,True, models.getQuestionFromURL(id).image_urlQ)

                self.redirect('/ReviewQuestion?id=' + id)
        # no image to upload
        except IndexError:
            id = self.request.get('id')
            explanation = models.getQuestionFromURL(id).explanation
            if not explanation:
                explanation = "No Explanation Provided"
            category = models.getQuestionFromURL(id).category
            creator = models.getQuestionFromURL(id).creator
            questionIn = self.request.get('questiontext')
            answer1 = self.request.get('answer1')
            answer2 = self.request.get('answer2')
            answer3 = self.request.get('answer3')
            answer4 = self.request.get('answer4')
            answerid = self.request.get('answerid')
            logging.warning(explanation)
            logging.warning(category)
            logging.warning(creator)
            logging.warning(questionIn)
            logging.warning(answer1)
            logging.warning(answer2)
            logging.warning(answer3)
            logging.warning(answer4)
            logging.warning('Signed by anonymous user')
            models.updateQuestion(id,category,questionIn,answer1,answer2,answer3,answer4,answerid,explanation,creator,True, models.getQuestionFromURL(id).image_urlQ)
                #models.update_profile(id, name, year, interests, bio, employer, models.get_User(id).image_url)

        self.redirect('/ReviewQuestion?id=' + id)

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

#Handles everything that happens on the profile page
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
                models.update_profile(id, name, year, interests, bio, employer, models.get_User(id).image_url)

            self.redirect('/profile?id=' + id)
        # no image to upload
        except IndexError:
            id = get_user_id()
            name = self.request.get("name")
            year = self.request.get("year")
            interests = self.request.get("interests")
            employer = self.request.get("employer")
            bio = self.request.get("bio")
            models.update_profile(id, name, year, interests, bio, employer, models.get_User(id).image_url)

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

#Processes the AJAX post for updating of the answer selected by the user in a quiz
class answerSingle(webapp2.RequestHandler):
    def post(self):
        self.response.headers.add_header('Access-Control-Allow-Origin', '*')
        self.response.headers['Content-Type'] = 'application/json'
        logging.warning("WHAT UP")
        logging.warning(self.request.body)
        data = json.loads(self.request.body)
        logging.warning(data['userID'])
        logging.warning(data['qKey'])
        question = models.getQuestionFromURL(data['qKey'])
        logging.warning(data['userSelection'])
        models.createAnswer(data['userID'],question.key,str(data['userSelection']), 10)

def obj_dict(obj):
    return obj.__dict__

#Fetches the quiz and passes the questions and relevant information to the page.
class categoryQuiz(webapp2.RequestHandler):
    def get(self):
        is_admin = 0
        if users.is_current_user_admin():
            is_admin = 1
        category = self.request.get('category')
        number = self.request.get('number')
        logging.warning(category)
        logging.warning(number)
        logging.warning(int(number))
        questions = models.getQuestionsCat(category,int(number))

        if questions:
            qList = []
            for q in questions:
                temp = q.to_dict(exclude=['image_urlQ','category','creator','accepted','up_voters','down_voters','create_date'])
                qList.append(temp)
            jList = json.dumps(qList, default=obj_dict)

            page_params = {
                'user_id': get_user_id(),
                'num': int(number),
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
        self.response.headers.add_header('Access-Control-Allow-Origin', '*')
        self.response.headers['Content-Type'] = 'application/json'
        data = json.loads(self.request.body)
        comment = data['comment']
        body = "Comment:\n" + comment
        sender_address = get_user_email() #not sure if we want to do this
        question = data['urlkey']
        body = body + "\n\nVisit the question here: aecs1980qg.appspot.com/ReviewQuestion?id=" + question
        subject = "A question has been reported"
        mail.send_mail(sender_address , "bogdanbg24@gmail.com" , subject, body)

class LeaderBoard(webapp2.RequestHandler):
    def get(self):
        render_template(self, 'leaderboard.html')

#Upvoting a question
class addVote(webapp2.RequestHandler):
    def post(self):
        id = self.request.get("id")
        email = get_user_email()
        models.addVote(id,email)
        time.sleep(1)
        self.redirect("/ReviewNewQuestions") #maybe want a confirmation page

#Downvoting a question
class decVote(webapp2.RequestHandler):
    def post(self):
        id = self.request.get("id")
        email = get_user_email()
        models.decVote(id,email)
        time.sleep(1)
        self.redirect("/ReviewNewQuestions")

#Upvoting a question
class addVoteQuiz(webapp2.RequestHandler):
    def post(self):
        self.response.headers.add_header('Access-Control-Allow-Origin', '*')
        self.response.headers['Content-Type'] = 'application/json'
        data = json.loads(self.request.body)
        id = data['urlkey']
        email = get_user_email()
        result = {}
        temp = models.addVote(id,email)
        logging.warning(temp)
        result['incced'] = temp
        logging.warning(result)
        self.response.out.write(json.dumps(result))

#Downvoting a question
class decVoteQuiz(webapp2.RequestHandler):
    def post(self):
        self.response.headers.add_header('Access-Control-Allow-Origin', '*')
        self.response.headers['Content-Type'] = 'application/json'
        data = json.loads(self.request.body)
        id = data['urlkey']
        email = get_user_email()
        temp = models.decVote(id,email)
        result = {}
        result['decced'] = temp
        self.response.out.write(json.dumps(result))

class deleteQuestion(webapp2.RequestHandler):
    def post(self):
        logging.warning("here")
        key = self.request.get(id)
        models.delete_question(key)
        self.redirect("/ReviewOldQuestions")

###############################################################################
mappings = [
  ('/', MainPageHandler),
  ('/profile', ProfileHandler),
  ('/submitNew', SubmitPageHandler),
  ('/NewQuestion', NewQuestion),
  ('/ReviewQuestion', ReviewSingleQuestion),
  ('/deleteQuestion', deleteQuestion),
  ('/meanstackakalamestack', test),
  ('/ReviewNewQuestions', ReviewNewQuestions),
  ('/ReviewOldQuestions', ReviewOldQuestions),
  ('/answerSingle',answerSingle),
  ('/report', reportHandler),
  ('/reportQuiz', reportQuizHandler),
  ('/incrementVote' , addVote),
  ('/decrementVote', decVote),
  ('/addVoteQuiz', addVoteQuiz),
  ('/decVoteQuiz', decVoteQuiz),
  ('/image', ImageHandler),
  ('/imageQ', ImageHandlerQuestion),
  ('/takeQuiz', categoryQuiz),
  ('/firstLogin', LoginPageHandler),
  ('/leaderboard', LeaderBoard)
]
app = webapp2.WSGIApplication(mappings, debug=True)
