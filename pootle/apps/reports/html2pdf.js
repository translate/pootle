var system = require('system')
var page = require('webpage').create();
var fs = require('fs');

var infile = system.args[1];
var outfile = system.args[2];

page.viewportSize = { width: 600, height: 600 };
page.paperSize = { format: 'Letter', orientation: 'portrait', margin: '1cm' };
page.zoomFactor = 1.3;

page.open(infile, function (status) {
  if (status !== 'success') {
    console.log('Failed to load the file');
  } else {
    page.render(outfile);
  }
  phantom.exit();
});
