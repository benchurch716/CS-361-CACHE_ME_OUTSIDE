import requests
from json import loads

def getImgUrl(searchTerm):
    url = 'http://flip3.engr.oregonstate.edu:3081/api'
    params = {
        'searchTerm': searchTerm
    }
    responseBody = requests.get(url, params=params).text
    imgUrl = loads(responseBody)['url']
    print('The url for the image is :' + imgUrl, flush=True)
    return imgUrl

def getLocationText(searchTerm):
    url = 'http://flip3.engr.oregonstate.edu:2405/api'
    jsonObj = {}
    jsonObj['wiki'] = searchTerm
    responseBody = requests.post(url, json=jsonObj).text
    locationText = loads(responseBody)['summary']
    return locationText