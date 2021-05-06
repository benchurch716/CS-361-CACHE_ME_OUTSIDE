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

//Home page
app.get('/', function (req, res, next) {
  var context = {};
  context.pageTitle = "Home";
  res.render('Home', context);
});

app.get('/result', function (req, res, next) {
  var context = {};
  context.pageTitle = "Result";
  context.data = 
  res.render('Result', context);
});

app.get('/noresult', function (req, res, next) {
  var context = {};
  context.pageTilte = "No Result";
  res.render('NoResult', context);
});

app.get('/apidoc', function (req, res, next) {
  var context = {};
  context.pageTitle = "API Documentation";
  res.render('APIdoc', context);
});


async function fetchImageName(searchTerm) {
  try {
    var urlString = "https://en.wikipedia.org/w/api.php?action=query&format=json&prop=pageimages&pilicense=free&titles=";
    var res = await fetch(urlString + searchTerm);
    const data = await res.json();
    return data;
  } catch (error) {
    console.log("Something went wrong with fetchImageName", error);
  }
}

async function fetchImageInfo(fileName) {
  try {
    var urlString = "https://en.wikipedia.org/w/api.php?action=query&format=json&prop=imageinfo&iiprop=url&titles=File:";
    var res = await fetch(urlString + fileName);
    const data = await res.json();
    return data;
  } catch (error) {
    console.log("Something went wrong with fetchImageInfo", error);
  }
}

app.post('/result', function (req, res, next) {
  var context = {};
  var pageid;
  context.searchTerm = req.body.searchTerm;
  fetchImageName(context.searchTerm)
    .then((data) => {
      pageid = Object.keys(data.query.pages);
       if (pageid == -1 || !data.query.pages[pageid].thumbnail) {
        res.render('NoResult', context);
      }
      else {
        context.fileName = data.query.pages[pageid].pageimage;
        console.log(context.fileName);
      }
    })
    .then(result => fetchImageInfo(context.fileName))
    .then((data) => {
      context.url = data.query.pages[Object.keys(data.query.pages)].imageinfo[0].url;
      console.log(context.url);
    })
    .then(() => {
        res.render('Result', context);
    })
    .catch((error) => {
      console.log("Something went wrong when posting to /result", error);
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