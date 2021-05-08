var express = require('express');
var app = express();
var handlebars = require('express-handlebars').create({ defaultLayout: 'main' });
var bodyParser = require('body-parser');
var fetch = require('node-fetch');

app.use(bodyParser.urlencoded({ extended: true }));
app.use(bodyParser.json());
app.engine('handlebars', handlebars.engine);
app.set('view engine', 'handlebars');
app.set('port', 3080);
app.use('/static', express.static('public'));

/* 
Sets context key/value pairs for the image url, width, height, description url, artist, license, and title.
Receives the image scraper context set and the response data from Wikipedia's API.
Returns the appended context.
*/
async function setValuesWithImageInfo(context, data) {
  try {
    const prefix = data.query.pages[Object.keys(data.query.pages)].imageinfo[0];
    if (prefix.thumburl) {
      context.url = prefix.thumburl;
      context.width = prefix.thumbwidth;
      context.height = prefix.thumbheight;
    } else {
      context.url = prefix.url;
      context.width = prefix.width;
      context.height = prefix.height;
    }
    context.descriptionURL = prefix.descriptionurl;
    context.artist = prefix.extmetadata.Artist.value;
    context.licenseShortName = prefix.extmetadata.LicenseShortName.value;
    context.title = prefix.extmetadata.ObjectName.value;  
    return context;
  } catch (error) {
    console.log("Something went wrong with setValuesWithImageInfo", error);
    next(error);
    return;
  }
}

// Home page
app.get('/', function (req, res, next) {
  var context = {};
  context.pageTitle = "Image Scraper Microservice GUI";
  res.render('Home', context);
});

// Displays the image result
app.get('/result', function (req, res, next) {
  var context = {};
  context.pageTitle = "Image Scraper Microservice GUI - Results";
  res.render('Result', context);
});

// Informs the user that no free images were found
app.get('/noresult', function (req, res, next) {
  var context = {};
  context.pageTilte = "Image Scraper Microservice GUI - No Results";
  res.render('NoResult', context);
});

// Image Scraper API documentation
app.get('/apidoc', function (req, res, next) {
  var context = {};
  context.pageTitle = "API Documentation";
  res.render('APIdoc', context);
});

// Queries to this address will deliver JSON data of the specified image
app.get('/api', function (req, res, next) {
  var context = {};
  var urlString;
  var urlImageInfo = "https://en.wikipedia.org/w/api.php?action=query&format=json&prop=imageinfo&iiprop=url|extmetadata|user|size&titles=File:";
  var urlPageImages = "https://en.wikipedia.org/w/api.php?action=query&format=json&prop=pageimages&pilicense=free&titles=";
  var pageid;
  var noImageFound = false;
  var q = req.query;
  context.searchTerm = q.searchTerm;
  fetch(urlPageImages+context.searchTerm) // Queries the Wikipedia API to get the file name of the specified subject
    .then((res) => res.json())
    .then((data) => {
      pageid = Object.keys(data.query.pages)
      if (pageid == -1 || !data.query.pages[pageid].thumbnail) { // In this case, no free images of the specifed subject were found
        noImageFound = true;
        context.noResult = "Could not find any free images of the specified search term";
        throw new Error('No free image results'); // Throws an error and goes straight to 'catch'
      } else {
        context.fileName = data.query.pages[pageid].pageimage
      }      
    })
    .then(result => {
      if (q.width) { // Width was specified
        urlString = urlImageInfo+context.fileName+"&iiurlwidth="+q.width;
      }
      else if (q.height) { // Only height was specified (defaults to width if both dimensions are specified)
        urlString = urlImageInfo+context.fileName+"&iiurlheight="+q.height;
      } else {  // No size was specified
        urlString = urlImageInfo+context.fileName;
      }
    })
    .then(result => fetch(urlString)) // Fetch the image info properties using the file name
    .then((res) => res.json())
    .then((data) => setValuesWithImageInfo(context, data))  // Use this data to set the rest of the context properties
    .then((data) => {
      context = data;
      if (q.pixelation) {
        context.pixelation = q.pixelation;
        // CODE TO HANDLE PIXELATION GOES HERE
      } else {
        context.pixelation = 0;
      }
      res.json(context);  // Send JSON data with the image results
    })
    .catch((error) => {
      console.log("Something went wrong with the /result post request", error);
      if (noImageFound == true) {
        res.json(context);  // Send JSON data informing the user that no free images were found
      } else {
        next(error)
      }
      return;
    })
});

// Displays the image results and associated details
app.post('/result', function (req, res, next) {
  var context = {};
  var urlString;
  var urlImageInfo = "https://en.wikipedia.org/w/api.php?action=query&format=json&prop=imageinfo&iiprop=url|extmetadata|user|size&titles=File:";
  var urlPageImages = "https://en.wikipedia.org/w/api.php?action=query&format=json&prop=pageimages&pilicense=free&titles=";
  var pageid;
  var noImageFound = false;
  var b = req.body;
  context.searchTerm = b.searchTerm;
  context.pixelation = b.pixelation;
  fetch(urlPageImages+context.searchTerm) // Queries the Wikipedia API to get the file name of the specified subject
    .then((res) => res.json())
    .then((data) => {
      pageid = Object.keys(data.query.pages)
      if (pageid == -1 || !data.query.pages[pageid].thumbnail) { // In this case, no free images of the specifed subject were found
        noImageFound = true;
        throw new Error('No free image results'); // Throws an error and goes straight to 'catch'
      } else {
        context.fileName = data.query.pages[pageid].pageimage
      }      
    })
    .then(result => {
      if (b.width) { // Width was specified
        urlString = urlImageInfo+context.fileName+"&iiurlwidth="+b.width;
      }
      else if (req.body.height) { // Only height was specified (defaults to width if both dimensions are specified)
        urlString = urlImageInfo+context.fileName+"&iiurlheight="+b.height;
      } else {  // No size was specified
        urlString = urlImageInfo+context.fileName;
      }
    })
    .then(result => fetch(urlString)) // Fetch the image info properties using the file name
    .then((res) => res.json())
    .then((data) => setValuesWithImageInfo(context, data))  // Use this data to set the rest of the context properties
    .then((data) => {
      context = data;
      if (b.pixelation) {
        context.pixelation = b.pixelation;
        // CODE TO HANDLE PIXELATION GOES HERE
      } else {
        context.pixelation = 0;
      }
      res.render('Result', context);  // Display the resulting image and its associated information
    })
    .catch((error) => {
      console.log("Something went wrong with the /result post request", error);
      if (noImageFound == true) {
        res.render('NoResult', context);  // Inform the user that no images were found
      } else {
        next(error)
      }
      return;
    })
});

app.use(function (req, res) {
  res.status(404);
  res.render('404');
});

app.use(function (err, req, res, next) {
  console.error(err.stack);
  res.status(500);
  res.render('500');
});

app.listen(app.get('port'), function () {
  console.log('Express started on http://flip3.engr.oregonstate.edu:' + app.get('port') + '; press Ctrl-C to terminate.');
});