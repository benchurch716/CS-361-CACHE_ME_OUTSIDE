// This file contains handlers for the Edit and Delete buttons on the Location pages.

// Delete a review. Called by Delete button.
function deleteReview(id) {
    // Ask user to confirm deletion
    var proceed = confirm('You\'re about to delete a review. Click Ok to continue.');
    if (!proceed) {
        return;
    }

    // Define callback function for HTTP Request
    var xhttp = new XMLHttpRequest();
    xhttp.onreadystatechange = function() {
        
        // On success, delete review from page
        if (this.readyState == 4 && this.status == 200) {
            jsonResponse = JSON.parse(this.responseText);
            containerId = "container_review" + jsonResponse.id;
            var container = document.getElementById(containerId);
            container.remove();
            return;
        }
        // On error, display alert
        else if (this.readyState == 4 && this.status != 200) {
        alert('Delete was unsuccessful')
        return;
        }
    }

    // Create and send HTTP request to server
    xhttp.open("POST", "/deleteReview", true);
    xhttp.setRequestHeader("Content-Type", "application/json");
    var body = {
        "id" : id
    }
    xhttp.send(JSON.stringify(body));
}


// Return the location page to its previous state. Called by Cancel button.
function cancelEdit(id) {
    spanId = "reviewText" + id;
    divId = "formDiv" + id;
    originalSpan = document.getElementById(spanId);
    newDiv = document.getElementById(divId);

    originalSpan.style.visibility = "visible";
    newDiv.remove();
    return;
}


// Display form allowing client to update a review. Called by Edit button.
function editReview(id) {    
    // Get and store review text
    var reviewSpan = document.getElementById("reviewText" + id);
    var reviewText = reviewSpan.innerHTML;

    // Check that user isn't already in edit mode
    if (reviewSpan.style.visibility == "hidden") {
        return;
    }
    
    // Hide review span, display textarea instead
    reviewSpan.style.visibility = "hidden";
    let newDiv = document.createElement("div");
    newDiv.id = "formDiv" + id
    var url = "/process_submission";
    var formHTML = "<form id='form" + id + "' onsubmit='saveChanges(" + id + ");return false' >" +
        "<textarea id='newReview" + id + "'>" + reviewText + "</textarea>" +
        "<input type='button' onclick='cancelEdit(" + id + ")' value='Cancel'>" +
        "<input type='submit' value='Submit'>" +
        "</form>";
    newDiv.innerHTML = formHTML;
    reviewSpan.parentNode.appendChild(newDiv);
    return;
}


// Send review changes to server. Called by Submit button.
function saveChanges(id) {
    // Get new review text
    var textAreaId = "newReview" + id;
    var textAreaElement = document.getElementById(textAreaId);
    var newReview = textAreaElement.value;

    // Create and initialize new XMLHttpRequest
    var xhttp = new XMLHttpRequest();
    xhttp.onreadystatechange = function() {

        // On success, replace text in review span and remove form div
        if (this.readyState == 4 && this.status == 200) {

            // Get id and new review text from HTTP response
            var jsonResponse = JSON.parse(this.responseText);
            var reviewTextId = "reviewText" + jsonResponse.id;
            var newReview = jsonResponse.newReview;

            // Identify DOM elements to be updated
            var reviewSpan = document.getElementById(reviewTextId);
            var formDivId = "formDiv" + id;
            var formDiv = document.getElementById(formDivId);

            // Update DOM elements with new review. Remove text editing form.
            // TODO: Sanitize newReview (i.e, don't use innerHTML in case user submits
            // malicious js code as a review)
            formDiv.remove();
            reviewSpan.innerHTML = newReview;
            reviewSpan.style.visibility = "visible";
            return;
        }
        // On error, display alert
        else if (this.readyState == 4 && this.status != 200) {
            alert('Edit was unsuccessful');
            return;
        }
    }

    // Create and send HTTP request to server
    xhttp.open("POST", "/update_review", true);
    xhttp.setRequestHeader("Content-Type", "application/json");
    var body = {
        "id" : id,
        "newReview" : newReview
    };
    xhttp.send(JSON.stringify(body));
}