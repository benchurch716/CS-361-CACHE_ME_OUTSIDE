var express = require('express');
var app = express();
var handlebars = require('express-handlebars').create({ defaultLayout: 'main' });
var bodyParser = require('body-parser');

app.use(bodyParser.urlencoded({ extended: true }));
app.use(bodyParser.json());
app.engine('handlebars', handlebars.engine);
app.set('view engine', 'handlebars');
app.set('port', 3080);
app.use('/static', express.static('public'));

const fetchWikiData = async (searchTerm) => {
  try {
      const urlString = 'https://en.wikipedia.org/w/api.php?action=query&format=json&prop=pageimages&pilicense=free&titles=' + searchTerm;
      const res = await fetch(urlString); // insert the query url here
  const data = await res.json();
  console.log(data); //get more specific data with data.key
  return data;
  } catch (err) {
      console.log("fetchWikiData caught an error.", err)
  }
}

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

app.post('/result', function (req, res, next) {
  var context = {};
  var data =  fetchWikiData(req.body.searchTerm);
  if (data) {
    res.redirect('/result');
  }
  else {
    res.redirect('/noresult');
  }
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
  console.log('Express started on http://flip3.engr.oregonstate.edu/:' + app.get('port') + '; press Ctrl-C to terminate.');
});