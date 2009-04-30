<?xml version="1.0" encoding="UTF-8"?>
<?python
from pootle_app.templates import pootlepage
from pootle_misc.baseurl import m, l
?>
<!DOCTYPE html  PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<html xmlns:py="http://purl.org/kid/ns#" xml:lang="$uilanguage" lang="$uilanguage" dir="$uidir">
  <head>
    <title py:content="pagetitle">Pootle</title>
    <meta py:if="defined('meta_description')" name="description" content="${meta_description}" />
    <meta py:if="defined('keywords')" name="keywords" content="${', '.join(keywords)}" />
    <link rel="stylesheet" type="text/css" href="${m('style.css')}" />
    <link rel="shortcut icon" href="${m('favicon.ico')}" />
    <script type="text/javascript" src="${m('js/jquery/jquery.min.js')}"></script>
    <script py:if="defined('header_script')" py:replace="header_script()"></script>
  </head>
  <body class="home">
    <div id="wrapper">
      <div py:replace="pootlepage.header(links, sessionvars, instancetitle)"/>
      
      <div id="body">

	<div class="site-message" py:if="message">
	  <div class="info" py:if="message" py:content="XML(message)">Message</div>
	</div>

	<div id="nav-secondary">
	  <div py:if="defined('search_block')">${search_block()}</div>
	  <div py:if="defined('breadcrumbs_block')">${breadcrumbs_block()}</div>
	  <div py:if="defined('innernav_block')">${innernav_block()}</div>
	</div>

	<div py:if="defined('precontent_block')">${precontent_block()}</div>
	<div py:if="defined('content_block')">${content_block()}</div>
	<div py:if="defined('postcontent_block')">${postcontent_block()}</div>
		
      </div> <!--body-->
    </div> <!--wrapper-->
    
    <div py:replace="pootlepage.footer(links, uidir)"/>
    
    <script type="text/javascript" src="${m('js/sorttable.js')}"></script>
    <script type="text/javascript" src="${m('js/search.js')}"></script>
    <!--[if lt IE 7.]>
	<script defer type="text/javascript" src="${mediaurl}js/correctpng.js"></script>
	<![endif]-->
    <script py:if="defined('page_script')" py:replace="page_script()"></script>
  </body>
</html>
