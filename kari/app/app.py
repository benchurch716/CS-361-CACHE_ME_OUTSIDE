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

DB = 'app.db'

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


class serviceForm(FlaskForm):
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


# Execute SELECT Query
def execSelectQuery(dbName, query, qParams):
    conn = sqlite3.connect(dbName)
    cur = conn.cursor()
    if qParams != None:
        result = cur.execute(query, qParams).fetchall()
    else:
        result = cur.execute(query).fetchall()
    conn.close()
    return result


# Execute INSERT Query
def execInsertQuery(dbName, query, qParams):
    conn = sqlite3.connect(dbName)
    cur = conn.cursor()
    cur.execute(query, qParams)    
    conn.commit()
    conn.close()   


# Get search term for a given location
def getWikiSearchTerm(id):
    return execSelectQuery(DB, 'SELECT searchTerm FROM locations WHERE id = (?)', id)


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
    searchBox = searchForm()
    pics = [('find.png', '/browse'), ('share.png', '/review')]

    # TODO: Make function to choose random featured locations and retrieve their data
    #       from DB.
    # Each location needs city, state, country, img link, page link
    featuredLocs = [
        FeaturedLoc('Corvallis', 'OR', 'United States'), \
        FeaturedLoc('Redmond', 'WA', 'United States'), \
        FeaturedLoc('Grays Point', 'NSW', 'Australia')
        ]      

    for loc in featuredLocs: 
        locationId = execSelectQuery(DB, 'SELECT id FROM locations WHERE city = (?)', (loc.city,))[0]
        print('locationId is ' + str(locationId), flush=True)
        searchTerm = getWikiSearchTerm(locationId)
        loc.img = getImgUrl(searchTerm)

    return render_template(
        'home.html',
        nav=nav,
        searchBox=searchBox,
        serviceUrl=serviceUrl,
        featuredLocs=featuredLocs,
        pics=pics
    )


# Initialize dropdown choices
def initializeDropdown(field):
    choices = []
    queryResults = execSelectQuery(DB, 'SELECT DISTINCT ' + field + ' FROM locations', None)
    for loc in queryResults:
        choices.append((loc[0], loc[0]))
    choices.sort()
    choices.insert(0, ('', ''))             # Insert blank at top of menu
    return choices


# Submit a Review Page
@app.route('/review')
def review():
    form = reviewForm()
    form.city.choices = initializeDropdown('city')
    form.state.choices = initializeDropdown('state')
    form.country.choices = initializeDropdown('country')
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

    # Retrieve id of location that the user specified
    city = form.city.data
    state = form.state.data
    country = form.country.data
    locationId = execSelectQuery(DB, 'SELECT id FROM locations WHERE city = (?) AND state = (?) \
        AND country = (?)', (city, state, country))
    
    # Check for location validity
    if locationId == []:
        print('ERROR: Location with this city/state/country combination not found')
        abort(404)

    # Add review to database and close connection
    executeInsertQuery("INSERT INTO reviews (locationId, name, review) VALUES (?, ?, ?)", \
        (locationId[0][0], form.name.data, form.review.data))

    redirectUrl = '/location?city=' + city.replace(' ', '%20') + '&state=' \
            + state.replace(' ', '%20') + '&country=' + country.replace(' ', '%20')
    
    return redirect(redirectUrl, code=303)


# Search Results Page
@app.route('/search_results', methods=['GET', 'POST'])
def search():
    form = searchForm()

    # Initialize search text
    searchText = form.searchText.data
    searchText = '%' + searchText + '%'

    # Perform search of cities, states and countries columns
    # TODO: Make this work with full state name. Currently works only with state abbr.
    # ie, 'OR' returns a match, whereas 'Oregon' does not
    queries = (
        'SELECT * FROM locations WHERE city LIKE (?)',
        'SELECT * FROM locations WHERE state LIKE (?)',
        'SELECT * FROM locations WHERE country LIKE (?)'
    )
    cities = execSelectQuery(DB, queries[0], (searchText,))
    states = execSelectQuery(DB, queries[1], (searchText,))
    countries = execSelectQuery(DB, queries[2], (searchText,))
    
    # Build results list
    rawResults = cities + states + countries
    resultsWithLink = []
    for locationId, city, state, country, searchTerm in rawResults:
        url = '/location?city=' + city.replace(' ', '%20') + '&state=' \
            + state.replace(' ', '%20') + '&country=' + country.replace(' ', '%20')
        imgUrl = getImgUrl(searchTerm)
        resultsWithLink.append((locationId, city, state, country, url, imgUrl))

    # TODO: Remove duplicates from list (eg, New York City, New York would appear twice if
    # searching for 'New York'. This is unwanted behavior.)

    return render_template(
        'search_results.html',
        results=resultsWithLink,
        nav=nav,
        serviceUrl=serviceUrl,
    )


# Browse Page
@app.route('/browse')
def browse():
    locations = execSelectQuery(DB, 'SELECT * FROM locations', None)

    # Add link to locations
    locationsWithLink = []
    for locationId, city, state, country, searchTerm in locations:
        url = '/location?city=' + city.replace(' ', '%20') + '&state=' \
            + state.replace(' ', '%20') + '&country=' + country.replace(' ', '%20')
        imgUrl = getImgUrl(searchTerm)
        locationsWithLink.append((locationId, city, state, country, url, imgUrl))
    
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

    # Get locationId based on URL query string parameters
    query = 'SELECT id FROM locations WHERE city = (?)'
    locationId = execSelectQuery(DB, query, (city,))[0]

    # Get all reviews for this location and analyze their sentiment scores
    query = 'SELECT review, name, id FROM reviews WHERE locationId = (?)'
    reviews = execSelectQuery(DB, query, locationId)
    
    concatReviews = ''
    for review in reviews:
        concatReviews = concatReviews + review[0] + ' '
    scores = SentimentIntensityAnalyzer().polarity_scores(concatReviews)
    sentiment = getSentiment(scores['compound'])
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
        sentiment=sentiment,
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
# See https://github.com/cjhutto/vaderSentiment for more information on how the
# VADER tool (included in nltk library) calculates sentiment analysis scores
@app.route('/service', methods=['GET', 'POST'])
def service():
    form = serviceForm()

    descriptions = {
        'neg': 'Proportion of the text that has negative sentiment',
        'neu': 'Proportion of the text that is neutral',
        'pos': 'Proportion of the text that has positive sentiment',
        'compound': 'A normalized, weighted composite score for the text overall. Ranges \
                    between -1 (most negative) to 1 (most positive)',
        'sentiment': 'Overall sentiment, based on compound score. Below -0.05 is negative', 
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