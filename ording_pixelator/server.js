const express = require("express");
const app = express();
const path = require('path')
const ejs = require("ejs");
const bodyParser = require("body-parser");
const PORT = process.env.PORT || 5000

const Jimp = require("jimp");
var cloudinary = require('cloudinary').v2;
const http = require('http');
const request = require('request');

app.use(express.urlencoded({extended: true}));
app.use(express.json());

app.set('view engine', 'ejs');
app.set('views', path.join(__dirname, 'views'))
app.use(express.static('public'));
app.listen(PORT, () => console.log(`Listening on ${ PORT }`))

cloudinary.config({ 
    cloud_name: 'ordingi', 
    api_key: '515673646318212', 
    api_secret: 'c2IffhnqnncwB15wgLvFINyesTE' 
  });

const data = []
const search = []

app.get("/", function (req, res) {
    res.render('pages/home');
});

app.get("/results", function(req,res){
    res.render("pages/results", {data: data})
});

app.get("/apisearch", function(req,res) {
    res.render("pages/apisearch", {search: search});
});

app.post("/results", function (req, res) {
    async function pixel() {
        var amount = parseInt(req.body.pixel_level);
        var imgPath = __dirname + "/public/pixelatedimg.png";
        const image = await Jimp.read(req.body.imagename);
        image.pixelate(amount)
        .writeAsync(imgPath);

        cloudinary.uploader.upload(imgPath, 
            function(error, result) {
                var new_image = result.url;
                var old_image = req.body.imagename;
                var newItem = {new_image: new_image, old_image: old_image};
                data.push(newItem);
                console.log(new_image);
                res.redirect("/results");
                console.log(result.url, error)});
      }
    pixel()
});

app.get("/restart", function (req, res) {
    data.splice(0);
    search.splice(0);
    res.render("pages/restart");
});

app.post("/api", (req, res) => {
    async function api_pixel() {
        var amount = parseInt(req.body.pix_amount);
        var imgPath = __dirname + "/public/pixelatedimg.png";
        const image = await Jimp.read(req.body.urlString);
        image.pixelate(amount)
        .writeAsync(imgPath);

        cloudinary.uploader.upload(imgPath, 
            function(error, result) {
                var new_image = result.url;
                var new_item = {"new_url": new_image};
                console.log(new_image);
                res.send(new_item);
                console.log(result.url, error)});

      }
    api_pixel()
});
   
app.post("/apisearch", (req, res) => {
    var term = req.body.searchterm;
    function search_pixel() {
        request('http://flip3.engr.oregonstate.edu:3081/api?searchTerm=' + term, { json: true }, function (err, item, body) {
            if (err) { return console.log(err); }
            var new_item = {url:body.url, holder:1}
            search.push(new_item);
            res.redirect("/apisearch");
          });
        
        }
    search_pixel()
});

app.use(function (req, res){
    res.status(404);
    res.render("pages/404");
});

app.use(function (req,res){
    res.status(500);
    res.render("pages/500");
});

app.listen(3000, function () {
    console.log("Server is running on localhost3000. Enter ^C to close");
});
