from flask import Flask, request, render_template
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField
from wtforms.validators import DataRequired
from nltk import word_tokenize, FreqDist
from nltk.sentiment.vader import SentimentIntensityAnalyzer
import sqlite3

app = Flask(__name__)
app.config.from_pyfile('config.py')


# Forms
class reviewForm(FlaskForm):
    name = StringField('name', validators=[DataRequired()])
    review = TextAreaField('review', validators=[DataRequired()])


class apiForm(FlaskForm):
    inputText = TextAreaField('input text', validators=[DataRequired()])


# Get sentiment of text
def getSentiment(compound):
    if not isinstance(compound, float):
        return 0
    if compound <= -0.05:
        return 'negative'
    elif compound < 0.05:
        return 'neutral'
    else:
        return 'positive'


# Get word count of text
def getWordCount(text):
    wordList = text.split(' ')
    count = 0
    for word in wordList:
        if word != '':
            count = count + 1
    return count


# Get Top x most frequent words in the text
def getMostFrequent(text, count):
    tokens = word_tokenize(text)
    frequency = FreqDist(tokens)
    return frequency.most_common(count)


# Placeholder for info from Ben's service (Wikipedia info box scraper)
dummyInfoboxData = {
    'Population': '898,553',
    'Area': '225.08 sq mi',
    'Elevation': '902 ft',
    'Demonym(s)': 'Columbusite',
    'Time Zone': 'UTC-5 (EST)'
}

# Placeholder for info from Judy's service (Wikipedia text scraper)
wikiText = {
        'text': """The city of Columbus was named after 15th-century Italian explorer
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
    'Home': '/',
    'Top': '/top',
    'Browse': '/browse',
    'Submit a Review': '/review'
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
    submitURL = nav.get('Submit a Review')

    city = request.args.get('city')
    state = request.args.get('state')
    country = request.args.get('country')

    # Connect to database and create cursor
    conn = sqlite3.connect('app.db')
    cur = conn.cursor()

    # Get locationId based on URL query string parameters
    locationId = cur.execute('SELECT id FROM locations WHERE city = (?)', (city,)).fetchall()
    print('my thing is: %s' % (locationId[0]), flush=True)

    # Get all reviews for this location
    reviews = cur.execute('SELECT review FROM reviews WHERE locationId = (?)', locationId[0]).fetchall()
    print('my reviews are: %s' % (tuple(locationId),), flush=True)

    # TODO: Create function to display location name properly

    return render_template(
        'location.html',
        nav=nav,
        serviceUrl=serviceUrl,
        city=city,
        infoboxData=infoboxData,
        locationText=locationText,
        submitURL=submitURL,
        reviews=reviews)

()
# Sentiment/Text Analysis GUI
@app.route('/service', methods=['GET', 'POST'])
def service():

    form = apiForm()

    # See https://github.com/cjhutto/vaderSentiment for more information on how the
    # VADER tool (included in nltk library) calculates sentiment analysis scores
    descriptions = {
        'neg': 'Proportion of the text that has negative sentiment',
        'neu': 'Proportion of the text that is neutral',
        'pos': 'Proportion of the text that has positive sentiment',
        'compound': 'A normalized, weighted composite score for the text overall. Ranges \
                    between -1 (most negative) to 1 (most positive)',
        'sentiment': 'Overall sentiment, based on compound score. Below -0.05 is negative, \
                    -0.05 to 0.05 is neutral, and greater than 0.05 is positive',
        'word_count': 'Word Count',
        'most_frequent': 'Most frequently used words in the text'
    }

    displayResults = False
    txtInput = ''
    scores = {
        'neg': '-',
        'neu': '-',
        'pos': '-',
        'compound': '-' 
    }
    sentiment = '-'
    wordCount = '-'
    mostFrequent = '-'


    if request.method == 'POST':
        displayResults = True
        txtInput = form.inputText.data
        scores = SentimentIntensityAnalyzer().polarity_scores(txtInput)
        sentiment = getSentiment(scores.get('compound'))
        if sentiment == 0:
            sentiment = 'ERROR'
        wordCount = getWordCount(txtInput)
        mostFrequent = getMostFrequent(txtInput, 5)

    return render_template(
        'service.html',
        nav=nav,
        serviceUrl=serviceUrl,
        form=form,
        displayResults=displayResults,
        txtInput=txtInput,
        scores=scores,
        sentiment=sentiment,
        wordCount=wordCount,
        mostFrequent=mostFrequent,
        descriptions=descriptions
        )