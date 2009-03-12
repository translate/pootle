var W3CDOM = (document.createElement && document.getElementsByTagName);

window.onload = init;

function init()
{
	if (!W3CDOM) return;
	var divs = document.getElementsByTagName('div');
	for (var i=0;i<divs.length;i++)
	{
		if (divs[i].className.indexOf('autoexpand') != -1)
		{
			var divobj = divs[i];
			if (divobj.id.match("orig[0-9]+"))
			{
				divobj.rownum = parseInt(divobj.id.replace("orig", ""));
				divobj.partner = document.getElementById("trans"+divobj.rownum)
				divobj.editlink = document.getElementById("editlink"+divobj.rownum)
			}
			else if (divobj.id.match("trans[0-9]+"))
			{
				divobj.rownum = parseInt(divobj.id.replace("trans", ""));
				divobj.partner = document.getElementById("orig"+divobj.rownum)
				divobj.editlink = document.getElementById("editlink"+divobj.rownum)
			}
			else
			{
				divobj.rownum = -1;
			}
			divobj.contractedHeight = 50;
			divobj.expandedHeight = 999;
			divobj.makeexpanded = makeexpanded;
			divobj.makecontracted = makecontracted;
			divobj.expandaction = expandaction;
			divobj.contractaction = contractaction;
			divobj.autoexpandstate = 'mouse';
		}
	}
}

function makeexpanded()
{
	this.style.maxHeight = this.expandedHeight + 'px';
	if (this.offsetHeight >= this.expandedHeight)
		this.style.borderBottom = '1px dotted #999';
	else
		this.style.borderBottom = '0';
	if (this.editlink)
		this.editlink.style.display = 'inline';
}

function makecontracted()
{
	this.style.maxHeight = this.contractedHeight + 'px';
	if (this.offsetHeight >= this.contractedHeight)
		this.style.borderBottom = '1px dotted #999';
	else
		this.style.borderBottom = '0';
	if (this.editlink)
		this.editlink.style.display = 'none';
}

function expandaction()
{
	if (this.autoexpandstate == 'mouse')
	{
		this.makeexpanded();
		if (this.partner)
		{
			this.partner.makeexpanded();
		}
	}
}

function contractaction()
{
	if (this.autoexpandstate == 'mouse')
	{
		this.makecontracted();
		if (this.partner)
		{
			this.partner.makecontracted();
		}
	}
}

function timedexpansion(divid)
{
	var div = document.getElementById(divid);
	div.expandaction();
}

function timedcontraction(divid)
{
	var div = document.getElementById(divid);
	div.contractaction();
}

function mouseGoesOver()
{
	if (this.timeevent)
		clearTimeout(this.timeevent);
	if (this.partner)
		if (this.partner.timeevent)
			clearTimeout(this.partner.timeevent);
	this.timeevent = setTimeout('timedexpansion("'+this.id+'")', 500);
}

function mouseGoesOut()
{
	if (this.timeevent)
		clearTimeout(this.timeevent);
	if (this.partner)
		if (this.partner.timeevent)
			clearTimeout(this.partner.timeevent);
	this.timeevent = setTimeout('timedcontraction("'+this.id+'")', 1000);
}

function mouseClick()
{
	if (this.autoexpandstate == 'mouse')
	{
		this.autoexpandstate = 'seton';
		this.makeexpanded();
		if (this.partner)
		{
			this.partner.makeexpanded();
			this.partner.autoexpandstate = 'seton';
		}
	}
	else // if (this.autoexpandstate == 'seton')
	{
		this.autoexpandstate = 'mouse';
		this.makecontracted();
		if (this.partner)
		{
			this.partner.makecontracted();
			this.partner.autoexpandstate = 'mouse';
		}
	}	
}

function copyorigtranslation(elementNumber)
{
	var i = 0;
	var enelement = document.getElementById("orig-pure" + elementNumber + "." + 0);
	//no plurals
	var trelement = document.getElementById("areatrans" + elementNumber );
	if (trelement){
		trelement.value = enelement.value.replace("\n", "\\n\n", "g").replace("\t", "\\t", "g");
		trelement.focus();
		return;
	}

	//plurals
	trelement = document.getElementById("areatrans" + elementNumber + "." + i );
	while (trelement)
	{
		trelement.focus(); //it will go to the last one
		trelement.value = enelement.value.replace("\n", "\\n\n", "g").replace("\t", "\\t", "g");
		i++;
		trelement = document.getElementById("areatrans" + elementNumber + "." + i );
	}
}

var focusedElement;
function setfocusedelement(element)
{
	focusedElement = element;
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

