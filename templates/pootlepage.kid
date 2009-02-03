<?xml version="1.0" encoding="utf-8"?>
<?python
   from pootle_app.models import get_profile, suggestions_accepted_count, suggestions_pending_count, suggestions_reviewed_count, submissions_count
   from django.contrib.auth import REDIRECT_FIELD_NAME
   from django.contrib.auth.forms import AuthenticationForm
?>
<include xmlns:py="http://purl.org/kid/ns#">

    <div py:def="header(links, sessionvars, baseurl, instancetitle)" py:strip="True">
      <!-- start header -->
      <div id="nav-access">
        <a href="#nav-main" py:content="links.skip_nav">skip to navigation</a>
      </div>
        <?python
            header_attributes = {};
            if sessionvars.isopen:
                header_attributes = {'class':'logged-in'}
            if sessionvars.issiteadmin:
                header_attributes = {'class':'logged-in admin'}
        ?>

        <div id="header" py:attrs="header_attributes">
          <div>
            <h1><a href="/" title="${links.home}" py:content="instancetitle">Verbatim</a></h1>
            <div id="nav-main" class="yuimenubar">
              <div class="bd">
                <ul class="first-of-type">
                  <li class="yuimenubaritem"><a href="${baseurl}" py:content="links.home">Home</a></li>
                  <li class="yuimenubaritem"><a href="${baseurl}doc/${links.doclang}/index.html" py:content="links.doc">Docs &amp; Help</a></li>
                  <div py:if="sessionvars.issiteadmin" py:strip="True">
                    <li class="yuimenubaritem"><a href="${baseurl}admin/" py:content="links.admin">Admin</a></li>
                  </div>
                  <div py:if="sessionvars.isopen" py:strip="True">
                    <li class="yuimenubaritem"><a href="${baseurl}home/">My account</a></li>
                    <li class="yuimenubaritem"><a href="${baseurl}logout.html">Log out</a></li>
		  </div>
                  <div py:if="not sessionvars.isopen" py:strip="True">
                    <li class="yuimenubaritem"><a href="${baseurl}login.html"><span>Log in</span></a></li>
                  </div>
                </ul>
              </div>
            </div>	
          </div>
	</div>
        <!--TODO
        <h1 py:content="instancetitle">
            Distribution se Pootle
        </h1>
        -->
        <!-- end header -->
    </div>

    <div py:def="footer(links, baseurl, uidir)" py:strip="True">
      <!-- start footer -->
      <div id="footer" dir="${uidir}">
        <div id="footer-contents">
          <ul class="nav">
            <li><a href="${baseurl}" py:content="links.home">Home</a></li>
            <li><a href="${baseurl}doc/${links.doclang}/index.html" py:content="links.doc">Docs &amp; Help</a></li>
            <li><a href="${baseurl}about.html" py:content="links.about">About this Pootle Server</a></li>
          </ul>
        </div>
      </div>
      <!-- end footer -->
    </div>

    <div py:def="login_form(username_title, password_title, login_text, register_text, canregister, request, uilanguage, sessionvars)" py:strip="True">
      <!-- start login form -->
      <div py:if="not sessionvars.isopen" py:strip="True">
        <form action="/login.html?${REDIRECT_FIELD_NAME}=${request.path_info}" method="post" id="login-form">
	  <table>
	    <div py:content="XML(AuthenticationForm(None).as_table())" />
	  </table>
          <div>
	    <table align="right">
              <tr>
		<td><a href="/register.html"><span py:replace="register_text" /></a>&nbsp;&nbsp;</td>
		<td><input type="submit" name="Login" value="${login_text}" /></td>
	      </tr>
	    </table>
	  </div>
          <input type="hidden" name="islogin" value="true" /> 
	</form>
      </div>
      <!-- end login form -->
    </div>

    <div py:def="translationsummarylegend(legend)" id="translationsummarylegend">
      <div> <img src="/images/green-bar.png" alt="" />${legend.translated}</div>
      <div> <img src="/images/purple-bar.png" alt="" />${legend.fuzzy}</div>
      <div> <img src="/images/red-bar.png" alt="" />${legend.untranslated}</div>
    </div>

    <div py:def="userstatistics(user, statstext, statstitle)" id="userstatistics">
      <table>
        <tr>
          <th scope="row" py:content="statstext['suggaccepted']">Suggestions Accepted</th>
          <td>${suggestions_accepted_count(get_profile(user))}</td>
        </tr>
        <tr>
          <th scope="row" py:content="statstext['suggpending']">Suggestions Pending</th>
          <td>${suggestions_pending_count(get_profile(user))}</td>
        </tr>
        <tr>
          <th scope="row" py:content="statstext['suggreviewed']">Suggestions Reviewed</th>
          <td>${suggestions_reviewed_count(get_profile(user))}</td>
        </tr>
        <tr>
          <th scope="row" py:content="statstext['submade']">Submissions Made</th>
          <td>${submissions_count(get_profile(user))}</td>
        </tr>
      </table>
    </div>

    <div py:def="topcontributerstable(topstats, topstatsheading)" class="module-primary clear topcontributers">
      <div class="hd"><h2 py:contents="topstatsheading">Top Contributors</h2></div>
      <div class="bd">
        <div py:for="stats in topstats">
          <div class="statslist">
            <h3 py:content="stats['headerlabel']">Top</h3>
            <ul py:for="(num, user) in enumerate(stats['data'])">
              <?python
                 if num % 2:
                   list_attributes = {'class': 'even'}
                 else:
                   list_attributes = {'class': 'odd'}
                 ?>
              <li py:attrs="list_attributes"><span class="name">${user.username}</span><span class="value">${user.num_contribs}</span></li>
	    </ul>
	  </div>
	</div>
      </div>
      <div class="ft clear"></div>
    </div>

</include>
