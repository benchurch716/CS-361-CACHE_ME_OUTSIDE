from flask import Flask, request, redirect, render_template, abort, make_response, jsonify, url_for
from flask.wrappers import Response
from werkzeug.exceptions import HTTPException
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField
from wtforms.validators import DataRequired
from nltk import word_tokenize, FreqDist, RegexpTokenizer
from nltk.sentiment.vader import SentimentIntensityAnalyzer
import sqlite3
import string
from wiki import *

app = Flask(__name__)
app.config.from_pyfile('config.py')


# Forms
class searchForm(FlaskForm):
    searchText = StringField('Search')
    actionUrl = '/search_results'

class reviewForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    city = SelectField('City', validators=[DataRequired()], validate_choice=False)
    state = SelectField('State', validate_choice=False)
    country = SelectField('Country', validators=[DataRequired()])
    review = TextAreaField('Review', validators=[DataRequired()])

class apiForm(FlaskForm):
    inputText = TextAreaField('Input Text', validators=[DataRequired()])


# Featured locations for home page
class FeaturedLoc:
    def __init__(self, city, state, country):
        self.city = city
        self.state = state
        self.country = country
        self.img = '/static/placeholder.jpg'
        self.page = '/location?city=' + city.replace(' ', '%20') + '&state=' \
            + state.replace(' ', '%20') + '&country=' + country.replace(' ', '%20')


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
    tokenizer = RegexpTokenizer(r'[A-Za-z]+')
    tokens = tokenizer.tokenize(text)
    frequency = FreqDist(tokens)
    return frequency.most_common(count)


# Get search term for a given location
def getWikiSearchTerm(id):
    conn = sqlite3.connect('app.db')
    cur = conn.cursor()
    print('id is : ' + str(id), flush=True)
    searchTerm = cur.execute('SELECT searchTerm FROM locations WHERE id = (?)', id).fetchall()
    conn.close()
    return searchTerm


# Navigation Bar - Label : Route
nav = {
    'Home': '/',
    'Browse Locations': '/browse',
    'Submit a Review': '/review'
}

serviceUrl = '/service'
searchResultsUrl = '/search_results'


# Home Page
@app.route('/')
def home():

    form = searchForm()

    # TODO: Make function to choose random featured locations and retrieve their data
    #       from DB.
    # Each location needs city, state, country, img link, page link
    featuredLocs = [FeaturedLoc('Redmond', 'WA', 'United States'), \
        FeaturedLoc('Corvallis', 'OR', 'United States'), \
        FeaturedLoc('Grays Point', 'NSW', 'Australia')
        ]

    for loc in featuredLocs:

        conn = sqlite3.connect('app.db')
        cur = conn.cursor()

        # Get locationId based on URL query string parameters
        locationId = cur.execute('SELECT id FROM locations WHERE city = (?)', (loc.city,)).fetchall()[0]        
        searchTerm = getWikiSearchTerm(locationId)
        loc.img = getImgUrl(searchTerm)

    return render_template(
        'home.html',
        nav=nav,
        form=form,
        serviceUrl=serviceUrl,
        featuredLocs=featuredLocs
    )


# Submit a Review Page
@app.route('/review')
def review():

    # Connect to database and create cursor
    conn = sqlite3.connect('app.db')
    cur = conn.cursor()

    # Create form
    form = reviewForm()
    
    # Initialize form dropdown choices
    form.city.choices = []
    queryResults = cur.execute('SELECT DISTINCT city FROM locations').fetchall()
    for city in queryResults:
        form.city.choices.append((city[0], city[0]))
    form.city.choices.sort()        

    form.state.choices = []
    queryResults = cur.execute('SELECT DISTINCT state FROM locations').fetchall()
    for state in queryResults:
        form.state.choices.append((state[0], state[0]))
    form.state.choices.sort()
    #form.state.choices.insert(0, '')        # Insert blank choice, since state is optional

    form.country.choices = []
    queryResults = cur.execute('SELECT DISTINCT country FROM locations').fetchall()
    for country in queryResults:
        form.country.choices.append((country[0], country[0]))
    form.country.choices.sort()                        

    return render_template(
        'review.html',
        nav=nav,
        serviceUrl=serviceUrl,
        form=form
    )


# This routing handles submission of user reviews
@app.route('/process_submission', methods=['POST'])
def process():

    form = reviewForm()
    conn = sqlite3.connect('app.db')
    cur = conn.cursor()    

    # Retrieve id of location that the user specified
    city = form.city.data
    state = form.state.data
    country = form.country.data
    locationId = cur.execute('SELECT id FROM locations WHERE city = (?) AND state = (?) \
        AND country = (?)', (city, state, country)).fetchall()
    
    # Check for location validity
    if locationId == []:
        print('ERROR: Location with this city/state/country combination not found')
        abort(404)

    # Add review to database and close connection
    cur.execute("INSERT INTO reviews (locationId, name, review) VALUES (?, ?, ?)", \
        (locationId[0][0], form.name.data, form.review.data))
    conn.commit()
    conn.close()

    redirectUrl = '/location?city=' + city.replace(' ', '%20') + '&state=' \
            + state.replace(' ', '%20') + '&country=' + country.replace(' ', '%20')
    
    return redirect(redirectUrl, code=303)


# Search Results Page
@app.route('/search_results', methods=['GET', 'POST'])
def search():

    form = searchForm()

    # Connect to database and create cursor
    conn = sqlite3.connect('app.db')
    cur = conn.cursor()

    # Initialize search text
    searchText = form.searchText.data
    searchText = '%' + searchText + '%'

    # Override default case-sensitive LIKE
    cur.execute('PRAGMA case_sensitive_like=OFF')
    conn.commit()

    # Perform search of cities, states and countries columns
    # TODO: Make this work with full state name. Currently works only with state abbr.
    # ie, 'OR' returns a match, whereas 'Oregon' does not    
    cities = cur.execute( 'SELECT * FROM locations WHERE city LIKE (?)', \
        (searchText,)).fetchall()
    states = cur.execute('SELECT * FROM locations WHERE state LIKE (?)', \
         (searchText,)).fetchall()      
    countries = cur.execute('SELECT * FROM locations WHERE country LIKE (?)', \
         (searchText,)).fetchall()
    
    # Build results list
    rawResults = cities + states + countries
    resultsWithLink = []
    for locationId, city, state, country, searchTerm in rawResults:
        url = '/location?city=' + city.replace(' ', '%20') + '&state=' \
        + state.replace(' ', '%20') + '&country=' + country.replace(' ', '%20')
        imgUrl = getImgUrl(searchTerm)
        resultsWithLink.append((locationId, city, state, country, url, imgUrl))
    print(resultsWithLink)

    # TODO: Remove duplicates from list (eg, New York City, New York would appear twice if
    # searching for 'New York'. This is unwanted behavior.)

    # Reset case-sensitive LIKE back to default, then close db connection
    cur.execute('PRAGMA case_sensitive_like=ON')
    conn.commit()                           
    conn.close()

    return render_template(
        'search_results.html',
        results=resultsWithLink,
        nav=nav,
        serviceUrl=serviceUrl,
    )


# Browse Page
@app.route('/browse')
def browse():

    # Connect to database and create cursor
    conn = sqlite3.connect('app.db')
    cur = conn.cursor()

    # Return list of all locations in database
    locations = cur.execute('SELECT * FROM locations').fetchall()

    # Add link to locations
    locationsWithLink = []
    for locationId, city, state, country, searchTerm in locations:
        url = '/location?city=' + city.replace(' ', '%20') + '&state=' \
        + state.replace(' ', '%20') + '&country=' + country.replace(' ', '%20')
        locationsWithLink.append((locationId, city, state, country, url))
    print(locationsWithLink)

    # Close db connection
    conn.commit()                           
    conn.close()
    
    return render_template(
        'browse.html',
        nav=nav,
        serviceUrl=serviceUrl,
        locations=locationsWithLink)


# Location Page
@app.route('/location', methods=['GET', 'POST'])
def location():

    submitURL = nav.get('Submit a Review')

    city = request.args.get('city')
    state = request.args.get('state')
    country = request.args.get('country')

    # Connect to database and create cursor
    conn = sqlite3.connect('app.db')
    cur = conn.cursor()

    # Get locationId based on URL query string parameters
    locationId = cur.execute('SELECT id FROM locations WHERE city = (?)', (city,)).fetchall()[0]

    # Get all reviews for this location and analyze their sentiment scores
    reviews = cur.execute('SELECT review, name, id FROM reviews WHERE locationId = (?)', locationId).fetchall()
    conn.close()
    
    concatReviews = ''
    for review in reviews:
        concatReviews = concatReviews + review[0] + ' '
    scores = SentimentIntensityAnalyzer().polarity_scores(concatReviews)
    reviewCount = len(reviews)

    # TODO: Fix this
    reviews.reverse()

    # TODO: Create function to display location name properly

    # Get information from Wikipedia scraper services
    searchTerm = getWikiSearchTerm(locationId)
    locationText = getLocationText(searchTerm)
    imgUrl = getImgUrl(searchTerm)

    return render_template(
        'location.html',
        nav=nav,
        serviceUrl=serviceUrl,
        city=city,
        locationText=locationText,
        submitURL=submitURL,
        scores=scores,
        reviewCount=reviewCount,
        reviews=reviews,
        imgUrl=imgUrl
    )


# Delete a review
@app.route('/deleteReview', methods=['POST'])
def deleteReview():
    # TODO: Validate id
    id = request.json['id']
    conn = sqlite3.connect('app.db')
    cur = conn.cursor()
    success = cur.execute('DELETE FROM reviews WHERE id = (?)', (id,))
    conn.commit()
    conn.close()
    return make_response({'success':True, 'id':id}, 200)


# Update a review
@app.route('/update_review', methods=['POST'])
def updateReview():
    # TODO: Validate id
    id = request.json['id']
    newReview = request.json['newReview']

    conn = sqlite3.connect('app.db')
    cur = conn.cursor()
    success = cur.execute('UPDATE reviews SET review = (?) WHERE id = (?)', (newReview, id))
    conn.commit()
    conn.close()

    return make_response({'success':True, 'id':id, 'newReview':newReview}, 200)


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
        'most_frequent': 'Most frequently used words and number of appearances in the text'
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


# Error handler for GUI
@app.errorhandler(404)
def pageNotFound(e):
    return render_template('404.html')


# API implementation    
@app.route('/api', methods=['GET', 'POST'])
def api():

    # Check for request type, content type
    if request.method == 'GET':
        return make_response({'error': 'Method Not Allowed'}, 405)
    if request.content_type != 'application/json':
        return make_response({'error': 'Unsupported Media Type'}, 415)

    else:
        # Check for request body in correct format
        try:
            txtInput = request.json['text']
        except:
            return make_response({'error': 'Bad Request'}, 400)

        # Create API response
        scores = SentimentIntensityAnalyzer().polarity_scores(txtInput)
        sentiment = getSentiment(scores.get('compound'))
        if sentiment == 0:
            sentiment = 'ERROR'
        wordCount = getWordCount(txtInput)
        mostFrequent = getMostFrequent(txtInput, 5)
        return jsonify(sentiment=sentiment,
                        compound=scores.get('compound'),
                        pos=scores.get('pos'),
                        neu=scores.get('neu'),
                        neg=scores.get('neg'),
                        wordCount=wordCount,
                        mostFrequent=mostFrequent,
                        )