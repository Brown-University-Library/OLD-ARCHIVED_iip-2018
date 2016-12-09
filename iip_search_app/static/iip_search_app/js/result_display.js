(function(){

var xmlURL = "/view_xml/";

var regex25Words = /((?:\s*[^\s]+){0,25})/; //should use \b but JS doesn't like \b and non-ascii chars

var Conv = new CETEI();

function display(domTarget) {
    $.get(xmlURL + domTarget.id + '/', function(data) {
        Conv.domToHTML5(data,function(parsed, self) {
            var transcription = $(parsed).find("tei-div[subtype=transcription]");
            console.log(parsed);
            var diplomatic = $(parsed).find("tei-div[subtype=diplomatic]");
            if (transcription.text().trim()) {
                $(domTarget).find(".transcription").append(transcription);
            } else if(diplomatic.text().trim()) {
                $(domTarget).find(".transcription .short_header").text("Diplomatic");
                $(domTarget).find(".transcription").append(diplomatic);
            } else {
                $(domTarget).find(".transcription").append("<tei-div>[no transcription]</tei-div>");
            }

            var translation = $(parsed).find("tei-div[type=translation]");
            if (translation.text().trim()) {
                $(domTarget).find(".translation").append(translation);
            } else {
                $(domTarget).find(".translation").append("<tei-div>[no translation]</tei-div>");
            }
        });
    }, 'xml');   
}

$("#search_results tr[id]").each( function() {
    display(this);
});

})();
