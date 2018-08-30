
//User 1604128 is IIP
var user = "1604128";
//Collection U2J49649 is also called IIP
var collection = "U2J49649";
//IIP Group
var GROUP = "180188";

function retrieve_bib (id_list, callback) {
	var tags = id_list.join(" || ");
	var req = new XMLHttpRequest();
	req.open("GET", "https://api.zotero.org/groups/" + GROUP + "/items?tag=" + tags + "&format=atom&content=bib,json", true);
	req.setRequestHeader("Zotero-API-Version", "2");
	req.onload = callback;
	req.send();
}

var bibliographies = {};

function render_bibliography() {
	var bib_entries = $("span.z_id");
	var id_list = [];
	for (var i = 0; i < bib_entries.length; i++) {
		var b = bib_entries[i].textContent.split("|");
		var new_id = b[0].trim();
		if(id_list.indexOf(new_id) == -1) {
			id_list.push(new_id);
		}
	}
	retrieve_bib(id_list, function() {
		if(this.status == 200) {
			var data = this.responseXML;
			var entries = data.documentElement.getElementsByTagName('entry');
			for (var i = 0; i < entries.length; i++) {
				var contents;
				var contents_f = entries[i].getElementsByTagName("content")[0];
				if(contents_f.children) {
					contents = contents_f.children;
				} else {
					contents = contents_f.getElementsByTagName("subcontent");
				}
				var entryjson = JSON.parse(contents[1].textContent);
				bibliographies[entryjson.archiveLocation] = {};
				bibliographies[entryjson.archiveLocation].parsed = entryjson;
				bibliographies[entryjson.archiveLocation].full = contents[0].textContent;
				bibliographies[entryjson.archiveLocation].url = entries[i].getElementsByTagName("id")[0].textContent;
			}

			$("li.biblToRetrieve").each(function() {
				
				var bspan = $(this).find('span')[0];
				b = bspan.innerHTML.trim();

				var pages = $(this).find('ul li');
				var new_html;

				try {
					new_html = bibliographies[b].full + "<br/>";
				}
				catch(err) {
					new_html = b + " (Citation not found in Zotero!)";
					bspan.innerHTML = new_html;
					pages.each(function() {
						var entry = $(this).text().split("|");
						if (entry[0] == "page") {
							$(this).text("Page " + entry[1]);
						} else {
							$(this).text("Inscription " + entry[1]);
						}
					});
					return;
				}
				this.attributes.class.value = "";

				if(pages.length !== 0) new_html += "(";
				var semicolon = "; ";
				for (var i = 0; i < pages.length; i++) {
					if(i == pages.length - 1) {
						semicolon = "";
					}
					var entry = pages[i].innerHTML.split("|");
					if(entry[0] == 'page') {
						new_html += "Page " + entry[1] + semicolon;
					} else {
						new_html += entry[1] + semicolon;
					}
				}
				if(pages.length !=+ 0) new_html += ")<br/>";
				$(this).find("ul")[0].innerHTML = "";
				if(bibliographies[b].url) new_html += "<a href='" + bibliographies[b].url + "'>Link to Full Entry</a>";

				bspan.innerHTML = new_html;
				
			});
			$("span.biblToRetrieve").each(function() {
				var b = this.innerHTML.split("|");
				try {
					var entry = bibliographies[b[0]].parsed;
					var colon = ": ";
					if(b[2] === "") colon = "";
					this.innerHTML = entry.creators[0].lastName + ". " + entry.title + ", " + entry.date + colon + b[2] + " (<a href='" + bibliographies[b[0]].url + "'>Full</a>)";
				}
				catch(err) {
					if(b[0] == "ms") {
						this.innerHTML = "Supplied by Michael Satlow";
					} else {
						var txt = b[0] + " ";
						if (b[1] == 'page') {
							txt += "Page " + b[2];
						} else {
							txt += "Inscription " + b[2];
						}
						this.innerHTML = txt + " (Citation Not Found)";
					}
				}
				this.attributes.class.value = "";
			});
		}
	});
}

$(document).ready(function(){
    $('.facetHeaderText').livequery(function(){
        $(this).click(function(event){
            $(this).toggleClass('facetMenuOpened');
            $(this).next('ul').toggle('30');
            });
    });

    $('#narrow_results a.showHideFacets').livequery(function(){
        $(this).click(function(event){
         event.preventDefault();
        $('.facetHeaderText').each(function(){
            $(this).toggleClass('facetMenuOpened');
            $(this).next('ul').toggle('30');
            });
        });            
    });


    $('.facetLink').livequery(function(){
        $(this).click(function(event){
                event.preventDefault();
                var isDisplayStatus = /display_status:.*/;
                //split the qstring into clauses
                var split_qstring = qstring.split(/\s+(?:AND|OR)\s+/);
                var newQStringParts = [];

                for (var i = 0; i < split_qstring.length; i++) {
                    if (!isDisplayStatus.test(split_qstring[i])) {
                        newQStringParts.push(split_qstring[i]);
                    }
                }
                newQStringParts.push($(this).attr('href') +':"'+$(this).attr('id') + '"');
                
                //Load the new results page
                window.location.search = "?q="+newQStringParts.join(" AND ") + "&resultsPage=1";
        });
    });
});

