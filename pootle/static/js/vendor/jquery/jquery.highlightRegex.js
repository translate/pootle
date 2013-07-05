/*
* jQuery Highlight Regex Plugin
*
* Based on highlight v3 by Johann Burkard
* http://johannburkard.de/blog/programming/javascript/highlight-javascript-text-higlighting-jquery-plugin.html
*
* (c) 2009 Jacob Rothstein
* MIT license
*/
(function($){
  $.fn.highlightRegex = function(regex) {
    if(regex == undefined || regex.source == '') {
      $(this).find('span.highlight').each(function(){
        $(this).replaceWith($(this).text());
        $(this).parent().each(function(){
          node = $(this).get(0);
          if(node.normalize) node.normalize();
        });
      });
    } else {
      $(this).each(function(){
        elt = $(this).get(0)
        elt.normalize();
        $.each($.makeArray(elt.childNodes), function(i, node){
          if(node.nodeType == 3) {
            var searchnode = node
            while((pos = searchnode.data.search(regex)) >= 0) {
              match = searchnode.data.slice(pos).match(regex)[0];
              if(match.length == 0) break;
              var spannode = document.createElement('span');
              spannode.className = 'highlight';
              var middlebit = searchnode.splitText(pos);
              var searchnode = middlebit.splitText(match.length);
              var middleclone = middlebit.cloneNode(true);
              spannode.appendChild(middleclone);
              searchnode.parentNode.replaceChild(spannode, middlebit);
            }
          } else {
            $(node).highlightRegex(regex);
          }
        })
      })
    }
    return $(this);
  }
})(jQuery);
