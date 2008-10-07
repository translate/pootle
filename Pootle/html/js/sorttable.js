/* 
 * Table sorting Javascript. MIT-licensed. Originally from 
 *
 *     http://www.kryogenix.org/code/browser/sorttable/
 * 
 * 2005-07-13: Initial import. Changed the arrow code to use the images
 *             included with Plone instead of the entities. Also changed
 *             the way sorting of a previously-sorted column behaves
 *             slightly. Reformatted to try keeping to 80 columns. (kiko)
 *
 * 2006-03-13: Added support for indicating sortkeys (direct and
 *             reverse) inside table cells. Removed tabs. (kiko)
 *
 * 2006-04-08: Fixed matching of "sortable". Added support for "initial-sort".
 *             Made sorting stable. (ddaa)
 *
 * 2006-04-11: Fixed numeric sorting to be robust in the presence of
 *             whitespace; added trim(). Note that parseFloat() deals
 *             with leading and trailing whitespace just fine. (kiko)
 *
 * 2006-04-12: Added default-sort and default-revsort classes. When
 *             the data in the table is already pre-sorted, you can use
 *             these classes to indicate by which column they were
 *             ordered by. This, in turn, allows us to correctly
 *             Javascript-sort them later. (kiko)
 *
 * 2006-07-14: Added ability to honour odd/even row colouring.  It is hackish
 *             as the styles are hardcoded and you get some screen jitter.
 *             Should most probably be part of the actual sort code to prevent
 *             the jittering. (dwayne)
 *
 */

addEvent(window, "load", sortables_init);

var SORT_COLUMN_INDEX;

/* the variable "baseurl" must be defined in any page including sorttable.js */
var arrowUp = baseurl + "images/up.png";
var arrowDown = baseurl + "images/down.png";
var arrowBlank = baseurl + "images/none.png";

function trim(str) {
    return str.replace(/^\s*|\s*$/g, "");
}

function sortables_init() {
    // Find all tables with class sortable and make them sortable
    if (!document.getElementsByTagName) return;
    tbls = document.getElementsByTagName("table");
    for (ti=0;ti<tbls.length;ti++) {
        thisTbl = tbls[ti];
        if (((' '+thisTbl.className+' ').indexOf(" sortable ") != -1) && 
             (thisTbl.id)) {
            ts_makeSortable(thisTbl);
        }
    }
}

function ts_makeSortable(table) {
    if (table.tHead && table.tHead.rows && table.tHead.rows.length > 0) {
        var firstRow = table.tHead.rows[0];
    } else if (table.rows && table.rows.length > 0) {
        var firstRow = table.rows[0];
    }
    if (!firstRow) return;

    // We have a first row: assume it's the header, and make its
    // contents clickable links
    for (var i=0;i<firstRow.cells.length;i++) {
        var cell = firstRow.cells[i];
        var txt = ts_getInnerText(cell);
        cell.innerHTML = '<a href="#" class="sortheader" onclick="ts_resortTable(this); return false;">' 
                         + txt + 
                         '<img class="sortarrow" src="'+arrowBlank+'" height="1" width="1"></a>';
    }

    // Sort by the first column whose title cell has initial-sort class.
    for (var i=0; i<firstRow.cells.length; i++) {
        var cell = firstRow.cells[i];
        var lnk = ts_firstChildByName(cell, 'A');
        var img = ts_firstChildByName(lnk, 'IMG')
        if ((' ' + cell.className + ' ').indexOf(" default-sort ") != -1) {
            ts_arrowDown(img);
            break;
        }
        if ((' ' + cell.className + ' ').indexOf(" default-revsort ") != -1) {
            ts_arrowUp(img);
            break;
        }
        if ((' ' + cell.className + ' ').indexOf(" initial-sort ") != -1) {
            ts_resortTable(lnk);
            break;
        }
    }
}

function ts_getInnerText(el) {
    if (typeof el == "string") return el;
    if (typeof el == "undefined") { return el };
    if (el.innerText) return el.innerText;    //Not needed but it is faster
    var str = "";

    var cs = el.childNodes;
    var l = cs.length;
    for (var i = 0; i < l; i++) {
        node = cs[i];
        switch (node.nodeType) {
            case 1: //ELEMENT_NODE
                if (node.className == "sortkey") {
                    return ts_getInnerText(node);
                } else if (node.className == "revsortkey") {
                    return "-" + ts_getInnerText(node);
                } else {
                    str += ts_getInnerText(node);
                    break;
                }
            case 3:    //TEXT_NODE
                str += node.nodeValue;
                break;
        }
    }
    return str;
}

function ts_firstChildByName(el, name) {
    for (var ci=0; ci < el.childNodes.length; ci++) {
        if (el.childNodes[ci].tagName && 
            el.childNodes[ci].tagName.toLowerCase() == name.toLowerCase())
            return el.childNodes[ci];
    }
}

function ts_arrowUp(img) {
    img.setAttribute('sortdir','up');
    img.src = arrowUp;
    img.height = 17
    img.width = 17
    img.alt = "up"
}

function ts_arrowDown(img) {
    img.setAttribute('sortdir','down');
    img.src = arrowDown;
    img.height = 17
    img.width = 17
    img.alt = "down"
}

function ts_arrowBlank(img) {
    img.setAttribute('sortdir','');
    img.src = arrowBlank;
    img.height = 1
    img.width = 1
//    img.alt = ""
}

function ts_resortTable(lnk) {
    // get the img
    var img = ts_firstChildByName(lnk, 'IMG')
    var td = lnk.parentNode;
    var column = td.cellIndex;
    var table = getParent(td,'TABLE');

    // Work out a type for the column
    if (table.rows.length <= 1) return;
    var itm = ts_getInnerText(table.rows[1].cells[column]);
    itm = trim(itm);

    sortfn = ts_sort_caseinsensitive;
    if (itm.match(/^\d\d[\/-]\d\d[\/-]\d\d\d\d$/)) sortfn = ts_sort_date;
    if (itm.match(/^\d\d[\/-]\d\d[\/-]\d\d$/)) sortfn = ts_sort_date;
    if (itm.match(/^[£$]/)) sortfn = ts_sort_currency;
    if (itm.match(/^-?[\d\.]+%?$/)) sortfn = ts_sort_numeric;

    SORT_COLUMN_INDEX = column;
    var firstRow = new Array();
    var newRows = new Array();
    for (i=0;i<table.rows[0].length;i++) { firstRow[i] = table.rows[0][i]; }
    for (j=1;j<table.rows.length;j++) {
        newRows[j-1] = table.rows[j];
        newRows[j-1].oldPosition = j-1;
    }

    newRows.sort(ts_stableSort(sortfn));

    if (img.getAttribute("sortdir") == 'down') {
        newRows.reverse();
        ts_arrowUp(img);
    } else {
        ts_arrowDown(img);
    }

    // We appendChild rows that already exist to the tbody, so it moves
    // them rather than creating new ones
    // don't do sortbottom rows
    for (i=0;i<newRows.length;i++) { 
        if (!newRows[i].className || 
            (newRows[i].className && 
             (newRows[i].className.indexOf('sortbottom') == -1)))
                table.tBodies[0].appendChild(newRows[i]);
    }
    // do sortbottom rows only
    for (i=0;i<newRows.length;i++) { 
        if (newRows[i].className && 
            (newRows[i].className.indexOf('sortbottom') != -1)) 
                table.tBodies[0].appendChild(newRows[i]);
    }

    for (i=0;i<newRows.length;i++) { 
        if (i % 2 == 0) {
                  table.tBodies[0].rows[i].className = ('item item-even')
        } else {
                  table.tBodies[0].rows[i].className = ('item item-odd')
        }
    }

    // Delete any other arrows there may be showing
    var allimgs = document.getElementsByTagName("img");
    for (var ci=0; ci<allimgs.length; ci++) {
        var one_img = allimgs[ci];
        if (one_img != img && 
            one_img.className == 'sortarrow' &&
            getParent(one_img, "table") == getParent(lnk, "table")) { 
                ts_arrowBlank(one_img)
//                one_img.src = arrowBlank;
//                one_img.setAttribute('sortdir', '');
        }
    }
}

function getParent(el, pTagName) {
    if (el == null) 
        return null;
    else if (el.nodeType == 1 && 
             el.tagName.toLowerCase() == pTagName.toLowerCase())
        // Gecko bug, supposed to be uppercase
        return el;
    else
        return getParent(el.parentNode, pTagName);
}

function ts_stableSort(sortfn) {
    // Return a comparison function based on sortfn, but using oldPosition
    // attributes to discriminate between objects that sortfn compares as
    // equal, effectively providing stable sort.
    function stableSort(a, b) {
        var cmp = sortfn(a, b);
        if (cmp != 0) {
            return cmp;
        } else {
                return a.oldPosition - b.oldPosition;
        }
    }
    return stableSort;
}

function ts_sort_date(a,b) {
    // y2k notes: two digit years less than 50 are treated as 20XX,
    // greater than 50 are treated as 19XX
    aa = trim(ts_getInnerText(a.cells[SORT_COLUMN_INDEX]));
    bb = trim(ts_getInnerText(b.cells[SORT_COLUMN_INDEX]));
    if (aa.length == 10) {
        dt1 = aa.substr(6,4)+aa.substr(3,2)+aa.substr(0,2);
    } else {
        yr = aa.substr(6,2);
        if (parseInt(yr) < 50) { yr = '20'+yr; } else { yr = '19'+yr; }
        dt1 = yr+aa.substr(3,2)+aa.substr(0,2);
    }
    if (bb.length == 10) {
        dt2 = bb.substr(6,4)+bb.substr(3,2)+bb.substr(0,2);
    } else {
        yr = bb.substr(6,2);
        if (parseInt(yr) < 50) { yr = '20'+yr; } else { yr = '19'+yr; }
        dt2 = yr+bb.substr(3,2)+bb.substr(0,2);
    }
    if (dt1==dt2) return 0;
    if (dt1<dt2) return -1;
    return 1;
}

function ts_sort_currency(a,b) { 
    aa = ts_getInnerText(a.cells[SORT_COLUMN_INDEX]).replace(/[^0-9.]/g,'');
    bb = ts_getInnerText(b.cells[SORT_COLUMN_INDEX]).replace(/[^0-9.]/g,'');
    return parseFloat(aa) - parseFloat(bb);
}

function ts_sort_numeric(a,b) {
    aa = parseFloat(ts_getInnerText(a.cells[SORT_COLUMN_INDEX]));
    if (isNaN(aa)) aa = 0;
    bb = parseFloat(ts_getInnerText(b.cells[SORT_COLUMN_INDEX])); 
    if (isNaN(bb)) bb = 0;
    return aa-bb;
}

function ts_sort_caseinsensitive(a,b) {
    aa = ts_getInnerText(a.cells[SORT_COLUMN_INDEX]).toLowerCase();
    bb = ts_getInnerText(b.cells[SORT_COLUMN_INDEX]).toLowerCase();
    if (aa==bb) return 0;
    if (aa<bb) return -1;
    return 1;
}

function ts_sort_default(a,b) {
    aa = ts_getInnerText(a.cells[SORT_COLUMN_INDEX]);
    bb = ts_getInnerText(b.cells[SORT_COLUMN_INDEX]);
    if (aa==bb) return 0;
    if (aa<bb) return -1;
    return 1;
}


// addEvent and removeEvent
// cross-browser event handling for IE5+, NS6 and Mozilla
// By Scott Andrew
function addEvent(elm, evType, fn, useCapture) {
    if (elm.addEventListener){
        elm.addEventListener(evType, fn, useCapture);
        return true;
    } else if (elm.attachEvent){
        var r = elm.attachEvent("on"+evType, fn);
        return r;
    } else {
        alert("Handler could not be removed");
    }
}

