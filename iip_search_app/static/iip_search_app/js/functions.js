$(document).ready(function(){
    $('#page_list a').livequery(function(){
        $(this).click(function(event){
                event.preventDefault();
                resultsPage = $(this).html();
                $.get('../search/', {'qstring':qstring,'resultsPage':resultsPage}, function(data){$('#paginated_results').replaceWith(data)});
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
                $.get('../search/', {'qstring':qstring,'resultsPage':1}, function(data){$('#paginated_results').replaceWith(data)});
        });
    });
    
    $('tr.short_result').livequery(function(){
        $(this).click(function(event){
                var p = $(this).next('tr.viewinscr');
                if(p.is(':hidden')){
                    $(this).find('td:eq(0)').addClass('loadingImg');
                    $.get(
                        "../viewinscr/"+$(this).attr('id')+"/", 
                        {'qstring':qstring,'resultsPage':resultsPage}, 
                        function(data){
                        p.find('td:eq(1)').html(data);
                        p.show();
                        p.prev('tr.short_result').hide();
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
