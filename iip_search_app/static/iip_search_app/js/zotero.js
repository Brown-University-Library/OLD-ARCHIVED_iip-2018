
//User 1604128 is IIP
var user = "1604128";
//Collection U2J49649 is also called IIP
var collection = "U2J49649";

function retrieve_bib (id_list, callback) {
	var tags = id_list.join(" || ");
	// $.ajax({
	// 	url: "https://api.zotero.org/users/" + user + "/collections/" + collection + "/items", 
	// 	data: {
	// 		"tag" : tags,
	// 		"format" : "atom",
	// 		"content" : "bib,json"
	// 	}, 
	// 	success: callback,
	// 	headers: {
	// 		"Zotero-API-Version" : "2",
	// 		"X-Requested-With" : "",
	// 	}});
	var req = new XMLHttpRequest();
	req.open("GET", "https://api.zotero.org/users/" + user + "/collections/" + collection + "/items?tag=" + tags + "&format=atom&content=bib,json", true);
	req.setRequestHeader("Zotero-API-Version", "2");
	req.onload = callback;
	req.send();
}

var bibliographies = {};


function render_bibliography() {
	var bib_entries = $("li.biblToRetrieve");
	var id_list = [];
	for (var i = 0; i < bib_entries.length; i++) {
		var b = bib_entries[i].innerText.split("|");
		if(id_list.indexOf(b[0]) == -1) {
			id_list.push(b[0]);
		};
	};
	retrieve_bib(id_list, function() {
		if(this.status == 200) {
			var data = this.responseXML;
			var entries = data.documentElement.getElementsByTagName('entry');
			for (var i = 0; i < entries.length; i++) {
				var contents = entries[i].getElementsByTagName("content")[0].getElementsByTagName('subcontent');
				var entryjson = JSON.parse(contents[1].innerHTML);
				bibliographies[entryjson.archiveLocation] = {};
				bibliographies[entryjson.archiveLocation]['parsed'] = entryjson;
				bibliographies[entryjson.archiveLocation]['full'] = contents[0].innerHTML;
				bibliographies[entryjson.archiveLocation]['url'] = entries[i].getElementsByTagName("id")[0].innerHTML;
			};

			$("li.biblToRetrieve").each(function() {
				var b = this.innerText.split("|");
				var ntype = "";
				if(b[1] === "insc") {
					ntype = "Inscription";
				} 
				if(b[1] === "page") {
					ntype = "Page";
				}
				try {
					this.innerHTML = "<br/>" +  bibliographies[b[0]]['full'] + "(" + ntype + " " + b[2] + ") <a href='" + bibliographies[b[0]]['url'] + "'>Full Entry</a><br/>";
				}
				catch(err) {
					this.innerHTML = "Bibliography Not Found";
				}
				this.attributes.class.value = "";
			});
			$("span.biblToRetrieve").each(function() {
				var b = this.innerText.split("|");
				try {
					var entry = bibliographies[b[0]]['parsed'];
					var colon = ": ";
					if(b[2] === "") colon = "";
					this.innerHTML = entry.creators[0]['lastName'] + ". " + entry.title + ", " + entry.date + colon + b[2] + " (<a href='" + bibliographies[b[0]]['url'] + "'>Full</a>)";
				}
				catch(err) {
					this.innerHTML = "Bibliography Not Found";
				}
				this.attributes.class.value = "";
			})
		}
	});
}

$(document).ready(function(){
    $('#page_list a').livequery(function(){
        $(this).click(function(event){
                event.preventDefault();
                resultsPage = $(this).html();
                $.get('../search_zotero/', {'qstring':qstring,'resultsPage':resultsPage}, function(data){$('#paginated_results').replaceWith(data)});
                $(this).css('color', '#000000').css('font-decoration', 'none');
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
                qstring = qstring+" AND "+$(this).attr('href') +':"'+$(this).html() + '"';
                $.get('../search_zotero/', {'qstring':qstring,'resultsPage':1}, function(data){$('#paginated_results').replaceWith(data)});
        });
    });
    
    $('tr.short_result').livequery(function(){
        $(this).click(function(event){
                var p = $(this).next('tr.viewinscr');
                if(p.is(':hidden')){
                    $(this).find('td:eq(0)').addClass('loadingImg');
                    $.get(
                        "../viewinscr_zotero/"+$(this).attr('id')+"/", 
                        {'qstring':qstring,'resultsPage':resultsPage}, 
                        function(data){
                        p.find('td:eq(1)').html(data);
                        p.show();
                        p.prev('tr.short_result').hide();
                        render_bibliography();
                        }
                     );
                }
               $(this).find('td:eq(0)').removeClass('loadingImg');
                p.click(function(){
                        $(this).prev('tr.short_result').show();
                        $(this).hide();
                    });
        });
    });
    
    $('.facetHeaderText').livequery(function(){
        $(this).click(function(event){
            $(this).toggleClass('facetMenuOpened');
            $(this).next('ul').toggle('30');
            });
    });
    
});

