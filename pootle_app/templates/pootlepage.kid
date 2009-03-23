<?xml version="1.0" encoding="utf-8"?>
<?python
   from pootle_app.models.suggestion import suggestions_accepted_count, suggestions_pending_count, suggestions_reviewed_count
   from pootle_app.models.submission import submissions_count
   from pootle_app.models.profile import get_profile
   from django.contrib.auth import REDIRECT_FIELD_NAME
   from django.contrib.auth.forms import AuthenticationForm
   from pootle_app.lib.util import l, m
?>
<include xmlns:py="http://purl.org/kid/ns#">

    <div py:def="header(links, sessionvars, instancetitle)" py:strip="True">
      <!-- start header -->
      <div id="nav-access">
        <a href="#nav-main" py:content="links.skip_nav">skip to navigation</a>
      </div>

      <div id="header">
        <div>
          <h1><a href="${l('/')}" title="${links.home}" py:content="instancetitle">Sitename</a></h1>
          <div id="nav-main" class="menubar">
            <div class="bd">
              <ul class="first-of-type">
                <li class="menubaritem"><a href="${l('/')}" py:content="links.home">Home</a></li>
                <li class="menubaritem"><a href="${m('doc/'+links.doclang+'/index.html')} " py:content="links.doc">Docs &amp; Help</a></li>
                <div py:if="sessionvars.issiteadmin" py:strip="True">
                  <li class="menubaritem"><a href="${l('/admin/')}" py:content="links.admin">Admin</a></li>
                </div>
                <div py:if="sessionvars.isopen" py:strip="True">
                  <li class="menubaritem"><a href="${l('/home/')}" py:content="links.account">My account</a></li>
                  <li class="menubaritem"><a href="${l('/logout.html')}" py:content="links.logout">Log out</a></li>
        </div>
                <div py:if="not sessionvars.isopen" py:strip="True">
                  <li class="menubaritem"><a href="${l('/register.html')}" py:content="links.register">Register</a></li>
                  <li class="menubaritem"><a href="${l('/login.html')}" py:content="links.login">Log in</a></li>
                </div>
              </ul>
            </div>
          </div>

        </div>
      </div>
      <!-- end header -->
    </div>

    <div py:def="footer(links, uidir)" py:strip="True">
      <!-- start footer -->
      <div id="footer" dir="${uidir}">
        <div id="footer-contents">
          <ul class="nav">
            <li><a href="${l('/')}" py:content="links.home">Home</a></li>
            <li><a href="${m('doc/'+links.doclang+'/index.html')}" py:content="links.doc">Docs &amp; Help</a></li>
            <li><a href="${l('/about.html')}" py:content="links.about">About this Pootle Server</a></li>
          </ul>
        </div>
      </div>
      <!-- end footer -->
    </div>

    <div py:def="translationsummarylegend(legend, mediaurl)" id="translationsummarylegend">
      <div> <img src="${m('/images/green-bar.png')}" alt="" />${legend.translated}</div>
      <div> <img src="${m('/images/purple-bar.png')}" alt="" />${legend.fuzzy}</div>
      <div> <img src="${m('/images/red-bar.png')}" alt="" />${legend.untranslated}</div>
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
