var express = require('express');
var CORS = require('cors');
var app = express();
var request = require('request'); // using request library (npm install request --save)

app.set('port', 2405);

app.use(express.json());
app.use(express.urlencoded({extended: false}));
app.use(CORS());

var apiurl = "https://en.wikipedia.org/w/api.php?origin=*&format=json&action=query&prop=extracts&exintro=&explaintext=&titles="

app.post('/api', function(req,res,next){
  // triggered when team member calls on my microservice
  // receives Wikipedia search term via POST API Request
  // returns JSON object containing key called "summary", value of scrapped Wikipedia summary based on the search term
  console.log("**Received POST Request for Wikipedia Summary Scrapper**");
  var {wiki} = req.body;
  var context = {};

  request(apiurl + wiki, function(err, response, body){
    if(err){
      next(err);
      return;
    }
    else{
      // unwrap the JSON data
      let wikiresponse = JSON.parse(body);
      let parsed_info = wikiresponse['query']['pages'];
      let id_num = Object.keys(parsed_info);
      let scrapped_data = parsed_info[id_num]['extract'];

      let data = {
        summary: scrapped_data
      };

    res.send(data)
    }
  })
});

app.post('/web_api', function(req,res,next){
  // triggered by user submitting Wikipedia search term from front end
  // calls on Kari's microservice to get overall connotation of scrapped Wikipedia summary
  // receives Wikipedia search term via POST Request
  // returns JSON object containing key called "summary", value of scrapped Wikipedia summary based on the search term + overall connotation
  console.log("**Received POST Request from front end**");
  var {wiki} = req.body;
  var context = {};
  var counter = 0;

  request(apiurl + wiki, function(err, response, body){
    if(err){
      next(err);
      return;
    }
    else{
      // unwrap the JSON data
      let wikiresponse = JSON.parse(body);
      let parsed_info = wikiresponse['query']['pages'];
      let id_num = Object.keys(parsed_info);
      let scrapped_data = parsed_info[id_num]['extract'];

      let my_data = {
        summary: scrapped_data
      };
      counter += 1

      if(counter = 1){
        // trigger call to Kari's microservice
        const data = {text: scrapped_data};

        const options = {
          url: 'http://flip3.engr.oregonstate.edu:9009/api', // note - need the "http://" part or else it won't run :)
          json: true,
          body: data,
          headers: {
            'Content-Type': 'application/json'
          }
        }

        request.post(options, function(err, request, body){
          if(err){
            return console.log(err);
          }
          else{
            let sentiment = body.sentiment;
            my_data.sentiment = sentiment;
            counter += 1
      
            if(counter = 2){
              console.log(my_data);
              res.send(my_data);
            }
          }
        });

      }
    }
  })
});


// referenced code from StackOverflow
// source: https://stackoverflow.com/questions/6158933/how-is-an-http-post-request-made-in-node-js

// function call_microservice(summary_data, counter){
//   console.log('reached call_microservice() fxn')
//   let summary = summary_data.summary
//   const data = {
//     text: summary
//   };

//   const options = {
//     url: 'http://flip3.engr.oregonstate.edu:9009/api', // note - need the "http://" part or else it won't run :)
//     json: true,
//     body: data,
//     headers: {
//       'Content-Type': 'application/json'
//     }
//   };
  
//   request.post(options, function(err, res, body){
//     if(err){
//       return console.log(err);
//     }
//     else{
//       //unwrap Kari's data
//       let sentiment = body.sentiment;
//       data.sentiment = sentiment;
//       counter += 1

//       if(counter = 2){
//         data.counter = 2
//         return data;
//       }
//     }
//   })
// };


app.use(function(req,res){
  console.log("404")
  res.status(404);
  res.send('404');
});

app.use(function(err, req, res, next){
  // console.error(err.stack);
  console.log("500")
  res.status(500);
  res.send('500');
});

app.listen(app.get('port'), function(){
  console.log('Express started on http://flip3.engr.oregonstate.edu:' + app.get('port') + '; press Ctrl-C to terminate.');
});