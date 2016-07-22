/*
  Modifications:
  Copyright 2013, 2104 Evernote Corporation

  ***

  SortTable
  version 2
  7th April 2007
  Stuart Langridge, http://www.kryogenix.org/code/browser/sorttable/

  Instructions:
  Download this file
  Add <script src="sorttable.js"></script> to your HTML
  Add class="sortable" to any table you'd like to make sortable
  Click on the headers to sort

  Thanks to many, many people for contributions and suggestions.
  Licenced as X11: http://www.kryogenix.org/code/browser/licence.html
  This basically means: do what you want with it.
*/


sorttable = {
  init: function() {
    if (!document.createElement || !document.getElementsByTagName) return;

    sorttable.DATE_RE = /^(\d\d?)[\/\.-](\d\d?)[\/\.-]((\d\d)?\d\d)$/;

    forEach(document.getElementsByTagName('table'), function(table) {
      if (table.className.search(/\bsortable\b/) != -1) {
        sorttable.makeSortable(table);
      }
    });

    makeZebra();

  },

  makeSortable: function(table) {
    if (table.getElementsByTagName('thead').length == 0) {
      // table doesn't have a tHead. Since it should have, create one and
      // put the first table row in it.
      the = document.createElement('thead');
      the.appendChild(table.rows[0]);
      table.insertBefore(the,table.firstChild);
    }
    // Safari doesn't support table.tHead, sigh
    if (table.tHead == null) table.tHead = table.getElementsByTagName('thead')[0];

    // Sorttable v1 put rows with a class of "sortbottom" at the bottom (as
    // "total" rows, for example). This is B&R, since what you're supposed
    // to do is put them in a tfoot. So, if there are sortbottom rows,
    // for backwards compatibility, move them to tfoot (creating it if needed).
    sortbottomrows = [];
    for (var i=0; i<table.rows.length; i++) {
      if (table.rows[i].className.search(/\bsortbottom\b/) != -1) {
        sortbottomrows[sortbottomrows.length] = table.rows[i];
      }
    }
    if (sortbottomrows) {
      if (table.tFoot == null) {
        // table doesn't have a tfoot. Create one.
        tfo = document.createElement('tfoot');
        table.appendChild(tfo);
      }
      for (var i=0; i<sortbottomrows.length; i++) {
        tfo.appendChild(sortbottomrows[i]);
      }
      delete sortbottomrows;
    }

    // work through each column and calculate its type
    headrow = table.tHead.rows[0].cells;
    for (var i=0; i<headrow.length; i++) {
      // manually override the type with a sorttable_type attribute
      if (!headrow[i].className.match(/\bsorttable_nosort\b/)) { // skip this col
        mtch = headrow[i].className.match(/\bsorttable_([a-z0-9]+)\b/);
        if (mtch) { override = mtch[1]; }
        if (mtch && typeof sorttable["sort_"+override] == 'function') {
          headrow[i].sorttable_sortfunction = sorttable["sort_"+override];
        } else {
         headrow[i].sorttable_sortfunction = sorttable.guessType(table,i);
        }

        // make it clickable to sort
        headrow[i].sorttable_columnindex = i;
        headrow[i].sorttable_tbody = table.tBodies[0];

        // Add unsorted icon
        unsorted = document.createElement('i');
        unsorted.className = "sorttable_unsorted icon-ascdesc";
        headrow[i].appendChild(unsorted);

        dean_addEvent(headrow[i],"click", function(e) {

          var cookieId = $(table).data('sort-cookie');

          if (this.className.search(/\bsorttable_sorted\b/) != -1) {
            // if we're already sorted by this column, just
            // reverse the table, which is quicker
            sorttable.reverse(this.sorttable_tbody);
            this.className = this.className.replace('sorttable_sorted',
                                                    'sorttable_sorted_reverse');
            this.removeChild(document.getElementById('sorttable_sortfwdind'));
            sortrevind = document.createElement('i');
            sortrevind.id = "sorttable_sortrevind";
            sortrevind.className = "icon-desc";
            this.appendChild(sortrevind);

            // Store current sorting criteria in a cookie
            sorttable.setSortCookie(cookieId, this.id, "desc");

            return;
          }

          if (this.className.search(/\bsorttable_sorted_reverse\b/) != -1) {
            // if we're already sorted by this column in reverse, just
            // re-reverse the table, which is quicker
            sorttable.reverse(this.sorttable_tbody);
            this.className = this.className.replace('sorttable_sorted_reverse',
                                                    'sorttable_sorted');
            this.removeChild(document.getElementById('sorttable_sortrevind'));
            sortfwdind = document.createElement('i');
            sortfwdind.id = "sorttable_sortfwdind";
            sortfwdind.className = "icon-asc";
            this.appendChild(sortfwdind);

            // Store current sorting criteria in a cookie
            sorttable.setSortCookie(cookieId, this.id, "asc");

            return;
          }

          sorttable.doSort(this);

          // Store current sorting criteria in a cookie
          sorttable.setSortCookie(cookieId, this.id, "asc");

        });
      }
    }
  },

  doSort: function(th) {
    // Remove sorttable_sorted classes
    theadrow = th.parentNode;
    forEach(theadrow.childNodes, function(cell) {
      if (cell.nodeType == 1) { // an element
        // Add unsorted icon if necessary as well
        if (cell.className.search(/\b(sorttable_sorted|sorttable_sorted_reverse)\b/) != -1) {
          unsorted = document.createElement('i');
          unsorted.className = "sorttable_unsorted icon-ascdesc";
          cell.appendChild(unsorted);
        }
        cell.className = cell.className.replace('sorttable_sorted_reverse','');
        cell.className = cell.className.replace('sorttable_sorted','');
      }
    });

    unsorted = $('.sorttable_unsorted', th).get(0);
    if (unsorted) { unsorted.parentNode.removeChild(unsorted); }
    sortfwdind = document.getElementById('sorttable_sortfwdind');
    if (sortfwdind) { sortfwdind.parentNode.removeChild(sortfwdind); }
    sortrevind = document.getElementById('sorttable_sortrevind');
    if (sortrevind) { sortrevind.parentNode.removeChild(sortrevind); }

    th.className += ' sorttable_sorted';
    sortfwdind = document.createElement('i');
    sortfwdind.id = "sorttable_sortfwdind";
    sortfwdind.className = "icon-asc";
    th.appendChild(sortfwdind);

    // build an array to sort. This is a Schwartzian transform thing,
    // i.e., we "decorate" each row with the actual sort key,
    // sort based on the sort keys, and then put the rows back in order
    // which is a lot faster because you only do getInnerText once per row
    row_array = [];
    col = th.sorttable_columnindex;
    rows = th.sorttable_tbody.rows;
    for (var j=0; j<rows.length; j++) {
      row_array[row_array.length] = [sorttable.getInnerText(rows[j].cells[col]), rows[j]];
    }
    /* If you want a stable sort, uncomment the following line */
    sorttable.shaker_sort(row_array, th.sorttable_sortfunction);
    /* and comment out this one */
    //row_array.sort(th.sorttable_sortfunction);

    tb = th.sorttable_tbody;
    for (var j=0; j<row_array.length; j++) {
      tb.appendChild(row_array[j][1]);
    }

    makeZebra();

    delete row_array;
  },

  guessType: function(table, column) {
    // guess the type of a column based on its first non-blank row
    sortfn = sorttable.sort_alpha;
    for (var i=0; i<table.tBodies[0].rows.length; i++) {
      text = sorttable.getInnerText(table.tBodies[0].rows[i].cells[column]);
      if (text != '') {
        if (text.match(/^-?[£$€]?[\d,.]+%?$/)) {
          return sorttable.sort_numeric;
        }
        // check for a date: dd/mm/yyyy or dd/mm/yy
        // can have / or . or - as separator
        // can be mm/dd as well
        possdate = text.match(sorttable.DATE_RE)
        if (possdate) {
          // looks like a date
          first = parseInt(possdate[1]);
          second = parseInt(possdate[2]);
          if (first > 12) {
            // definitely dd/mm
            return sorttable.sort_ddmm;
          } else if (second > 12) {
            return sorttable.sort_mmdd;
          } else {
            // looks like a date, but we can't tell which, so assume
            // that it's dd/mm (English imperialism!) and keep looking
            sortfn = sorttable.sort_ddmm;
          }
        }
      }
    }
    return sortfn;
  },

  getInnerText: function(node) {
    // gets the text we want to use for sorting for a cell.
    // strips leading and trailing whitespace.
    // this is *not* a generic getInnerText function; it's special to sorttable.
    // for example, you can override the cell text with a customkey attribute.
    // it also gets .value for <input> fields.

    hasInputs = (typeof node.getElementsByTagName == 'function') &&
                 node.getElementsByTagName('input').length;

    if (typeof node.getAttribute != 'undefined' && node.getAttribute("sorttable_customkey") != null) {
      return node.getAttribute("sorttable_customkey");
    }
    else if (typeof node.textContent != 'undefined' && !hasInputs) {
      return node.textContent.replace(/^\s+|\s+$/g, '');
    }
    else if (typeof node.innerText != 'undefined' && !hasInputs) {
      return node.innerText.replace(/^\s+|\s+$/g, '');
    }
    else if (typeof node.text != 'undefined' && !hasInputs) {
      return node.text.replace(/^\s+|\s+$/g, '');
    }
    else {
      switch (node.nodeType) {
        case 3:
          if (node.nodeName.toLowerCase() == 'input') {
            return node.value.replace(/^\s+|\s+$/g, '');
          }
        case 4:
          return node.nodeValue.replace(/^\s+|\s+$/g, '');
          break;
        case 1:
        case 11:
          var innerText = '';
          for (var i = 0; i < node.childNodes.length; i++) {
            innerText += sorttable.getInnerText(node.childNodes[i]);
          }
          return innerText.replace(/^\s+|\s+$/g, '');
          break;
        default:
          return '';
      }
    }
  },
  reverse: function(tbody) {
    // reverse the rows in a tbody
    newrows = [];
    for (var i=0; i<tbody.rows.length; i++) {
      newrows[newrows.length] = tbody.rows[i];
    }
    for (var i=newrows.length-1; i>=0; i--) {
       tbody.appendChild(newrows[i]);
    }
    delete newrows;
  },

  /* sort functions
     each sort function takes two parameters, a and b
     you are comparing a[0] and b[0] */
  sort_numeric: function(a,b) {
    aa = parseFloat(a[0].replace(/[^0-9.-]/g,''));
    if (isNaN(aa)) aa = 0;
    bb = parseFloat(b[0].replace(/[^0-9.-]/g,''));
    if (isNaN(bb)) bb = 0;
    return aa-bb;
  },
  sort_alpha: function(a,b) {
    if (a[0]==b[0]) return 0;
    if (a[0]<b[0]) return -1;
    return 1;
  },
  sort_ddmm: function(a,b) {
    mtch = a[0].match(sorttable.DATE_RE);
    y = mtch[3]; m = mtch[2]; d = mtch[1];
    if (m.length == 1) m = '0'+m;
    if (d.length == 1) d = '0'+d;
    dt1 = y+m+d;
    mtch = b[0].match(sorttable.DATE_RE);
    y = mtch[3]; m = mtch[2]; d = mtch[1];
    if (m.length == 1) m = '0'+m;
    if (d.length == 1) d = '0'+d;
    dt2 = y+m+d;
    if (dt1==dt2) return 0;
    if (dt1<dt2) return -1;
    return 1;
  },
  sort_mmdd: function(a,b) {
    mtch = a[0].match(sorttable.DATE_RE);
    y = mtch[3]; d = mtch[2]; m = mtch[1];
    if (m.length == 1) m = '0'+m;
    if (d.length == 1) d = '0'+d;
    dt1 = y+m+d;
    mtch = b[0].match(sorttable.DATE_RE);
    y = mtch[3]; d = mtch[2]; m = mtch[1];
    if (m.length == 1) m = '0'+m;
    if (d.length == 1) d = '0'+d;
    dt2 = y+m+d;
    if (dt1==dt2) return 0;
    if (dt1<dt2) return -1;
    return 1;
  },

  shaker_sort: function(list, comp_func) {
    // A stable sort function to allow multi-level sorting of data
    // see: http://en.wikipedia.org/wiki/Cocktail_sort
    // thanks to Joseph Nahmias
    var b = 0;
    var t = list.length - 1;
    var swap = true;

    while(swap) {
        swap = false;
        for(var i = b; i < t; ++i) {
            if ( comp_func(list[i], list[i+1]) > 0 ) {
                var q = list[i]; list[i] = list[i+1]; list[i+1] = q;
                swap = true;
            }
        } // for
        t--;

        if (!swap) break;

        for(var i = t; i > b; --i) {
            if ( comp_func(list[i], list[i-1]) < 0 ) {
                var q = list[i]; list[i] = list[i-1]; list[i-1] = q;
                swap = true;
            }
        } // for
        b++;

    } // while(swap)
  },

  /*
   * Saves the sorting order of `theadId` column in `cookieId`
   */
  setSortCookie: function (cookieId, theadId, sortOrder) {
    if (!cookieId || !theadId) {
      return;
    }

    var cookieData = JSON.stringify({columnId: theadId,
                                     order: sortOrder});
    PTL.cookie(cookieId, cookieData, { path: '/' });
  },

  /*
   * Retrieves the sorting order for `theadId` column in `cookieId`
   */
  getSortCookie: function (cookieId) {
    try {
      return JSON.parse(PTL.cookie(cookieId));
    } catch(e) {
      return {};
    }
  },

}

/* ******************************************************************
   Supporting functions: bundled here to avoid depending on a library
   ****************************************************************** */

// Dean Edwards/Matthias Miller/John Resig

document.addEventListener("DOMContentLoaded", sorttable.init, false);

// written by Dean Edwards, 2005
// with input from Tino Zijdel, Matthias Miller, Diego Perini

// http://dean.edwards.name/weblog/2005/10/add-event/

function dean_addEvent(element, type, handler) {
  if (element.addEventListener) {
    element.addEventListener(type, handler, false);
  } else {
    // assign each event handler a unique ID
    if (!handler.$$guid) handler.$$guid = dean_addEvent.guid++;
    // create a hash table of event types for the element
    if (!element.events) element.events = {};
    // create a hash table of event handlers for each element/event pair
    var handlers = element.events[type];
    if (!handlers) {
      handlers = element.events[type] = {};
      // store the existing event handler (if there is one)
      if (element["on" + type]) {
        handlers[0] = element["on" + type];
      }
    }
    // store the event handler in the hash table
    handlers[handler.$$guid] = handler;
    // assign a global event handler to do all the work
    element["on" + type] = handleEvent;
  }
};
// a counter used to create unique IDs
dean_addEvent.guid = 1;

function removeEvent(element, type, handler) {
  if (element.removeEventListener) {
    element.removeEventListener(type, handler, false);
  } else {
    // delete the event handler from the hash table
    if (element.events && element.events[type]) {
      delete element.events[type][handler.$$guid];
    }
  }
};

function handleEvent(event) {
  var returnValue = true;
  // get a reference to the hash table of event handlers
  var handlers = this.events[event.type];
  // execute each event handler
  for (var i in handlers) {
    this.$$handleEvent = handlers[i];
    if (this.$$handleEvent(event) === false) {
      returnValue = false;
    }
  }
  return returnValue;
};

// Dean's forEach: http://dean.edwards.name/base/forEach.js
/*
  forEach, version 1.0
  Copyright 2006, Dean Edwards
  License: http://www.opensource.org/licenses/mit-license.php
*/

// array-like enumeration
if (!Array.forEach) { // mozilla already supports this
  Array.forEach = function(array, block, context) {
    for (var i = 0; i < array.length; i++) {
      block.call(context, array[i], i, array);
    }
  };
}

// generic enumeration
Function.prototype.forEach = function(object, block, context) {
  for (var key in object) {
    if (typeof this.prototype[key] == "undefined") {
      block.call(context, object[key], key, object);
    }
  }
};

// character enumeration
String.forEach = function(string, block, context) {
  Array.forEach(string.split(""), function(chr, index) {
      block.call(context, chr, index, string);
  });
};

// globally resolve forEach enumeration
var forEach = function(object, block, context) {
  if (object) {
    var resolve = Object; // default
    if (object instanceof Function) {
      // functions have a "length" property
      resolve = Function;
    } else if (object.forEach instanceof Function) {
      // the object implements a custom forEach method so use that
      object.forEach(block, context);
      return;
    } else if (typeof object == "string") {
      // the object is a string
      resolve = String;
    } else if (typeof object.length == "number") {
      // the object is array-like
      resolve = Array;
    }
    resolve.forEach(object, block, context);
  }
};


/**
 * Manually adds odd row classes. This should be removed in favour of
 * `nth-child` selectors, but first the table needs to remove any non-visible
 * items.
 */
function makeZebra() {
  var rows = Array.prototype.slice.call(
    document.querySelectorAll('table.sortable tbody tr')
  );
  rows.forEach(function rmZebra(row, i) {
    row.classList.remove('odd');
  });

  var rows = Array.prototype.slice.call(
    document.querySelectorAll('table.sortable tbody tr.is-visible')
  );
  rows.forEach(function addZebra(row, i) {
    row.classList.toggle('odd', i % 2 === 0);
  });
}
