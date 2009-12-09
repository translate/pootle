
/*
 * TODO: this code may have a better life if we migrate it to jQuery.
 */
$(document).ready(function() {
    $(".focused").focus(function(e) {
        focusedElement = e.target;
    });

});

function copyorigtranslation(elementNumber)
{
	var i = 0;
    var enelement = document.getElementById("orig-pure" + elementNumber + "-" + 0);
    var envalue = enelement.value.replace("\n", "\\n\n", "g").replace("\t", "\\t", "g");
	//no plurals
	var trelement = document.getElementById("areatrans" + elementNumber );
	if (trelement){
		trelement.value = envalue;
		trelement.focus();
		return;
	}

	//plurals
	trelement = document.getElementById("areatrans" + elementNumber + "-" + i );
    var enplelement = document.getElementById("orig-pure" + elementNumber + "-" + 1);
    var enplvalue = enplelement.value.replace("\n", "\\n\n", "g").replace("\t", "\\t", "g");
	while (trelement)
	{
		trelement.focus(); //it will go to the last one
		trelement.value = i == 0 ? envalue : enplvalue;
		i++;
		trelement = document.getElementById("areatrans" + elementNumber + "-" + i );
	}
}

function writespecial(specialchar, elementnumber)
{
        //elementnumber will be something like "trans4"
	var element = document.getElementById("area" + elementnumber);
	if (focusedElement)
		insertatposition(focusedElement, specialchar, 0);
}

function insertatposition(element, text, rollback) 
{
	element.focus();
	if (navigator && navigator.appName == "Microsoft Internet Explorer")
	{
		document.selection.createRange().text = text;
	}
	else
	{
		var wholetext = element.value;
		var cursorposition = element.selectionStart;
		var finalposition = cursorposition + text.length - rollback;

		var before = wholetext.substr(0, cursorposition);
		var after = wholetext.substr(cursorposition, wholetext.length);
	
		element.value = before + text + after;
		element.setSelectionRange(finalposition, finalposition);
	}
}

