const express = require("express");
const app = express();
const ejs = require("ejs");
const bodyParser = require("body-parser");

const Jimp = require("jimp");

app.use(bodyParser.urlencoded({extended: true}));
app.set('view engine', 'ejs');

const data = []

app.get("/", function (req, res) {
    res.render('pages/home');
});

app.get("/results", function(req,res){
    res.render("pages/results", {data: data})
});

app.post("/results", function (req, res) {
    async function pixel() {
        var amount = parseInt(req.body.pixel_level);
        console.log(amount);
        const image = await Jimp.read(req.body.imagename);
        image.pixelate(amount)
        .write('pixelate1.png');
      }
    pixel()
    
    var new_image = '/home/ordingi/node_projects/pixel_project/pixelate1.png';
    var holder = 1;
    var newItem = {new_image: new_image, holder: holder};
    data.push(newItem);
    console.log(new_image);
    res.redirect("/results");
});

app.get("/send_DL", function (req, res) {
    res.render("pages/send_DL");
});

app.get("/restart", function (req, res) {
    data.splice(0);
    res.render("pages/restart");
});

app.listen(3000, function () {
    console.log("Server is running on localhost3000. Enter ^C to close");
});
