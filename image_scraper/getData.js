
const fetchWikiData = async (searchTerm) => {
    try {
        const urlString = 'https://en.wikipedia.org/w/api.php?action=query&format=json&prop=pageimages&pilicense=free&titles=' + searchTerm;
        const res = await fetch(urlString); // insert the query url here
    const data = await res.json();
    console.log(data); //get more specific data with data.key
    } catch (err) {
        console.log("fetchWikiData caught an error.", err)
    }
}