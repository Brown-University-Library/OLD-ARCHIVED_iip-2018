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
                $(domTarget).find(".transcription").html(transcription);
            } else if(diplomatic.text().trim()) {
                $(domTarget).find(".transcription").html(diplomatic);
            } else {
                $(domTarget).find(".transcription").html("[no transcription]");
            }

            var translation = $(parsed).find("tei-div[type=translation]");
            if (translation.text().trim()) {
                $(domTarget).find(".translation").html(translation);
            } else {
                $(domTarget).find(".translation").html("[no translation]");
            }
        });
    }, 'xml');   
}

$("#search_results tr[id]").each( function() {
    display(this);
});

})();
