// reference for how to call API: https://stackoverflow.com/questions/24806962/get-an-article-summary-from-the-mediawiki-api

//5-10-21:
// issues:
// - need to figure out how to replace existing results with new one (currently, the first result summary and 2nd result summary are smooshed together")
// - how to be able to scrap wiki pages with spaces (i.e. "John Cena")

baseURL = "https://en.wikipedia.org/w/api.php?origin=*&format=json&action=query&prop=extracts&exintro=&explaintext=&titles="
document.addEventListener('DOMContentLoaded', bindButton);

function bindButton(){
    // when user clicks on "submit" button on front-end, will trigger a POST request to the backend node.js server
    // node.js server will call on Wikipedia API and return scrapped data
    document.getElementById('userSubmit').addEventListener('click', function(event){
    console.log("clicked submit button");

    var req = new XMLHttpRequest();

    let data = {};
    data.wiki = document.getElementById("wikiLink").value;
    console.log("sent data:", data);

    req.open("POST", 'http://flip3.engr.oregonstate.edu:2405' + '/web_api', true);
    req.setRequestHeader('Content-Type', 'application/json');

    req.addEventListener('load', function(){
        if(req.status >= 200 && req.status < 400){
            console.log("Sent request from frontend!");
            if (req.responseText == null || req.responseText == ""){
                noResult();
            }
            else{
                let requested_data = JSON.parse(req.responseText)
                showResult(requested_data);
            }
        }
        else{
            console.log("Error in network request:" + req.statusText)
        }
    });
        req.send(JSON.stringify(data));
        event.preventDefault();
    });
}

function showResult(returned_data){
    // shows result of the Wikipedia scrapping to the webpage
    let resultsParagraph = document.getElementById("resultsHeader");
    resultsParagraph.innerHTML = returned_data.summary;

    // placeholder code for Kari's connotation result
    let connotation = document.getElementById("resultsConnotation");
    connotation.innerHTML = returned_data.sentiment;
    connotation.innerHTML.fontcolor("green");

    // change visibility to be "on" for Wiki summary and connotation
    // change visibility to be "off" for form
    let summaryDiv = document.getElementById("wikiSummary");
    let connotationDiv = document.getElementById("overallConnotation");
    let form = document.getElementById("userForm");


    summaryDiv.style.visibility = "visible";
    connotationDiv.style.visibility = "visible";
    form.style.visibility = "hidden"

    retryButton();

    console.log("finished showResults()");

}

function retryButton(){
    // after user successfully scrapes page and gets connotation, change visibility of "Scrape Something Else" button

    let retryButton = document.getElementById('retryButton');
    retryButton.style.visibility = "visible";

    retryButton.addEventListener('click', function(event){
        // clicking on button will refresh page and change visibility
            // hidden for wikiSummary, overallConnotation, retryButton
            // visible for userForm

        let summaryDiv = document.getElementById("wikiSummary");
        let connotationDiv = document.getElementById("overallConnotation");
        let form = document.getElementById("userForm");


        summaryDiv.style.visibility = "hidden";
        connotationDiv.style.visibility = "hidden";
        form.style.visibility = "visible"
        retryButton.style.visibility = "hidden";

        location.reload(true);
    });
}

function noResult(){
    // triggered when the user searches for a non-existing term or messes up the search item
    // console.log("rearched noResult()");
    // let errorText = "Error - Try Again!";
    // let resultsParagraph = document.getElementById("resultsHeader");
    // resultsParagraph.innerHTML = errorText;
    
    // send user to error.html
    window.location = "http://web.engr.oregonstate.edu/~leeju2/public/error.html"
}