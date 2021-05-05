from flask import Flask, request, render_template
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField
from wtforms.validators import DataRequired
from nltk.sentiment.vader import SentimentIntensityAnalyzer

app = Flask(__name__)
app.config.from_pyfile('config.py')

# Forms
class reviewForm(FlaskForm):
	name = StringField('name', validators=[DataRequired()])
	review = TextAreaField('review', validators=[DataRequired()])

class apiForm(FlaskForm):
	inputText = TextAreaField('input text', validators=[DataRequired()])	


# Placeholder for info from Ben's service (Wikipedia info box scraper)
dummyInfoboxData = {
	'Population' : '898,553',
	'Area' : '225.08 sq mi',
	'Elevation' : '902 ft',
	'Demonym(s)' : 'Columbusite',
	'Time Zone' : 'UTC-5 (EST)'
}

# Placeholder for info from Judy's service (Wikipedia text scraper)
wikiText = {
	'text' : """The city of Columbus was named after 15th-century Italian explorer 
				Christopher Columbus at the city's founding in 1812.[12] It is the largest 
				city in the world named for the explorer, who sailed to and settled parts 
				of the Americas on behalf of Isabella I of Castille and Spain. Although no 
				reliable history exists as to why Columbus, who had no connection to the 
				city or state of Ohio before the city's founding, was chosen as the name 
				for the city, the book Columbus: The Story of a City indicates a state 
				lawmaker and local resident admired the explorer enough to persuade other 
				lawmakers to name the settlement Columbus."""
}

# Navigation Bar - Label : Route
nav = {
	'Home' : '/',
	'Top' : '/top',
	'Browse' : '/browse',
	'Submit a Review' : '/review'
}

serviceUrl = '/service'


# Home Page
@app.route('/')
def home():
	return render_template('base.html', nav=nav, serviceUrl=serviceUrl)


# Submit a Review Page
@app.route('/review')
def review():
	form = reviewForm()
	return render_template('review.html', nav=nav, serviceUrl=serviceUrl, form=form)


# Top 5 Page
@app.route('/top')
def top():
	return render_template('top.html', nav=nav, serviceUrl=serviceUrl)


# Search Results Page
@app.route('/search_results')
def search():
	return render_template('search_results.html', nav=nav, serviceUrl=serviceUrl)


# Browse Page
@app.route('/browse')
def browse():
	return render_template('browse.html', nav=nav, serviceUrl=serviceUrl)


# Location Page
@app.route('/location')
def location():
	infoboxData = dummyInfoboxData
	locationText = wikiText.get('text')
	location = request.args.get('location')
	submitURL = nav.get('Submit a Review')
	return render_template('location.html', nav=nav, serviceUrl=serviceUrl, location=location, infoboxData=infoboxData, locationText=locationText, submitURL=submitURL)


# Sentiment/Text Analysis GUI
@app.route('/service', methods=['GET', 'POST'])
def service():
	displayResults = False
	txtInput = ''
	form = apiForm()
	if request.method == 'POST':
		displayResults = True
		txtInput = form.inputText.data
		scores = SentimentIntensityAnalyzer().polarity_scores(txtInput)
	return render_template('service.html', nav=nav, serviceUrl=serviceUrl, form=form, displayResults=displayResults, txtInput=txtInput)


# Note to self - This is what polarity_scores returns:
#sentiment_dict = \
#            {"neg": round(neg, 3),
#             "neu": round(neu, 3),
#             "pos": round(pos, 3),
#             "compound": round(compound, 4)}