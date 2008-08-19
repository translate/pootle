<?xml version="1.0" encoding="utf-8"?>
<include xmlns:py="http://purl.org/kid/ns#">
    <div py:def="banner(instancetitle, links, session, uidir, uilanguage, baseurl)" id="banner" lang="$uilanguage" dir="$uidir">
        <h1 py:content="instancetitle">
            Distribution se Pootle
        </h1>
        <div class="side">
            <a href="${baseurl}" py:content="links.home">Home</a> |
            <a href="${baseurl}projects/" py:content="links.projects">All Projects</a> |
            <a href="${baseurl}languages/" py:content="links.languages">All Languages</a>
            <span py:if="session.isopen" py:strip="True"> | <a href="${baseurl}home/" py:content="links.account">My account</a></span>
            <span py:if="session.issiteadmin" py:strip="True"> |
            <a href="${baseurl}admin/" py:content="links.admin">Admin</a> </span> |
            <a href="${baseurl}doc/${links.doclang}/index.html" py:content="links.doc">Docs &amp; Help</a>
        </div>
    </div>

    <div py:def="user_links(links, session, uidir, uilanguage, baseurl, block=None)" id="links" class="sidebar" dir="$uidir" lang="$uilanguage">
        <!--! Account information -->
        <div class="account">
            <div class="side">
                <img src="${baseurl}images/person.png" class="icon" alt="" dir="$uidir" lang="$uilanguage" />
            </div>
            <div class="side" py:if="session.isopen">
                <span py:content="XML(session.status)">logged in as <b>somebody</b></span> |
                <a href="${baseurl}?islogout=1" py:content="links.logout">Log Out</a>
            </div>
            <div class="side" py:if="not session.isopen">
              <a href="${baseurl}login.html" py:content="links.login">Log In</a> |
              <a href="${baseurl}register.html" py:content="links.register">Register</a> |
              <a href="${baseurl}activate.html" py:content="links.activate">Activate</a>
            </div>
        </div>
        <div py:if="block != None" py:replace="block"/>
    </div>

    <div py:def="about(aboutlink, uidir, uilanguage, baseurl)" id="about" dir="$uidir" lang="$uilanguage">
        <a href="${baseurl}about.html" py:content="aboutlink">About this Pootle server</a>
    </div>
</include>
