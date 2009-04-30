<?xml version="1.0" encoding="utf-8"?>
<?python
from pootle_misc.baseurl import l, m
?>
<include-this xmlns:py="http://purl.org/kid/ns#">
  <div py:def="item_block(item, uidir, uilanguage, mediaurl, block=None)" class="contentsitem">
    <img src="${m('/images/'+item.icon+'.png')}" class="icon" alt="" dir="$uidir" lang="$uilanguage" />
    <h3 py:if="item.title" id="itemtitle" class="title"><a href="${l(item.href)}">${item.title}</a></h3>
    <div py:if="block != None" py:replace="block"/>
    <div id="actionlinks" class="item-description" py:if="item.actions">
      <span py:for="i, link in enumerate(item.actions.basic)" py:strip="True">
        <a href="${l(link.href)}" title="${link.title}">${link.text}</a>
        <span py:if="i &lt; len(item.actions.basic) - 1" py:strip=""> | </span>
      </span>
      <form py:if="item.actions.goalform" action="" name="${item.actions.goalform.name}" method="post">
        <input type="hidden" name="editgoalfile" value="${item.actions.goalform.filename}"/>
        <select name="editgoal" py:attrs="multiple=item.actions.goalform.multifiles">
          <option value=""/>
          <option py:for="goalname in item.actions.goalform.goalnames" value="${goalname}" py:content="goalname" selected="${item.actions.goalform.filegoals[goalname]}">Goal</option>
        </select>
        <input py:if="item.actions.goalform.multifiles" type="hidden" name="allowmultikey" value="editgoal"/>
        <input type="submit" name="doeditgoal" value="${item.actions.goalform.setgoal_text}"/>
        <span py:if="item.actions.goalform.users" py:strip="True">
          <select name="editfileuser" py:attrs="multiple=item.actions.goalform.multiusers">
            <option value=""/>
            <option py:for="user in item.actions.goalform.users" value="${user}" py:content="user" selected="${item.actions.goalform.assignusers[user]}">Username</option>
          </select>
          <a py:if="not item.actions.goalform.multiusers" href="#" onclick="var userselect = document.forms.${item.actions.goalform.name}.editfileuser; userselect.multiple = true; return false" py:content="item.actions.goalform.selectmultiple_text">Select Multiple</a>
          <input type="hidden" name="allowmultikey" value="editfileuser"/>
          <select name="edituserwhich">
            <option py:for="a in item.actions.goalform.assignwhich" value="${a.value}">${a.text}</option>
          </select>
          <input type="submit" name="doedituser" value="${item.actions.goalform.assignto_text}"/>
        </span>
      </form>
      <span py:for="i, link in enumerate(item.actions.extended)" py:strip="True">
        <a href="${l(link.href)}" title="${link.title}">${link.text}</a>
        <span py:if="i &lt; len(item.actions.extended) - 1" py:strip=""> | </span>
      </span>
    </div>
  </div>

  <div py:def="itemstats(item)" class="item-statistics">
    <span py:if="item.stats.summary" py:replace="XML(item.stats.summary)">
      2/2 words (100%) translated <span class="string-statistics">[2/2 strings]</span>
    </span>
    <span py:for="check in item.stats.checks" py:strip="True">
      <br />
      <a href="${l(check.href)}" py:content="check.text">checkname</a>
      <span py:content="check.stats" py:strip="True">3 strings (20%) failed</span>
    </span>
    <span py:for="astats in item.stats.assigns" py:strip="True">
    <br /><a href="${l(astats.assign.href)}">${astats.assign.text}</a>: ${astats.stats}
      <span class='string-statistics'>${astats.stringstats}</span> -
      ${astats.completestats} <span class='string-statistics'>${astats.completestringstats}</span>
      <a py:if="astats.remove" href="${l(astats.remove.href)}">${astats.remove.text}</a>
    </span>
  </div>

  <div py:def="itemdata(item, uidir, uilanguage, mediaurl)">
    <td class="stats-name">
      <img src="${m('/images/'+item.icon+'.png')}" class="icon" alt="" dir="$uidir" lang="$uilanguage" />
      <a href="${l(item.href)}" lang="en" dir="ltr">${item.title}</a>
    </td>
    <span py:if="item.data" py:strip="True">
      <td class="stats">${item.data.translatedsourcewords}</td><td class="stats">${item.data.translatedpercentage}%</td>
      <td class="stats">${item.data.fuzzysourcewords}</td><td class="stats">${item.data.fuzzypercentage}%</td>
      <td class="stats">${item.data.untranslatedsourcewords}</td><td class="stats">${item.data.untranslatedpercentage}%</td>
      <td class="stats">${item.data.totalsourcewords}</td>
      <td class="stats-graph">
        <span class="sortkey">${item.data.translatedpercentage}</span>
        <table border="0" cellpadding="0" cellspacing="0"><tr>
            <td bgcolor="green" class="data" height="20" width="${item.data.translatedpercentage or int(bool(item.data.translatedsourcewords))}" />
            <td bgcolor="#d3d3d3" class="data" height="20" width="${item.data.fuzzypercentage or int(bool(item.data.fuzzysourcewords))}" py:if="item.data.fuzzysourcewords"/>
            <td bgcolor="red" class="data" height="20" width="${item.data.untranslatedpercentage or int(bool(item.data.untranslatedsourcewords))}" py:if="item.data.untranslatedsourcewords" />
        </tr></table>
      </td>
    </span>
  </div>

  <div py:def="itemsummary(item, uidir, untranslatedtext, fuzzytext, complete)" py:strip="True">
    <?python 
      if uidir == 'ltr':
        cssaligndir = 'left'
      else:
        cssaligndir = 'right'
    ?>
    <td class="stats-name">
      <a href="${l(item.href)}">${item.title}</a>
    </td>
    <span py:if="item.data" py:strip="True">
      <td class="stats-graph">
        <span class="sortkey">${item.data.translatedpercentage}</span>
        <span class="graph" title="${item.data.translatedpercentage}% complete" dir="$uidir">
            <span class="translated" style="width: ${item.data.translatedpercentage or int(bool(item.data.translatedsourcewords))}px" />
            <span class="fuzzy" style="${cssaligndir}: ${item.data.translatedpercentage or int(bool(item.data.translatedsourcewords))}px; width: ${item.data.fuzzypercentage or int(bool(item.data.fuzzysourcewords))}px" py:if="item.data.fuzzysourcewords"/>
            <span class="untranslated" style="${cssaligndir}: ${(item.data.translatedpercentage or int(bool(item.data.translatedsourcewords))) + (item.data.fuzzypercentage or int(bool(item.data.fuzzysourcewords)))}px; width: ${100 - ((item.data.translatedpercentage or int(bool(item.data.translatedsourcewords))) + (item.data.fuzzypercentage or int(bool(item.data.fuzzysourcewords))))}px" py:if="item.data.untranslatedsourcewords" />
        </span>
      </td>
      <td class="stats">
        <?python
            untranslatedwordstext = untranslatedtext % (item.data.untranslatedsourcewords)
            fuzzywordstext = fuzzytext % (item.data.fuzzysourcewords)

            # TODO: Need to verify these work for multiple files in the same directory.  It
            # might be showing all fuzzy files for the whole dir instead of per file
            untranslatedhref = "translate.html?match_names=untranslated&editing=1&view_mode=review"
            fuzzyhref = "translate.html?match_names=check-isfuzzy&editing=1&view_mode=review"

            # sigh; here is a cheesy hack.  If item.code exists we're at the root
            # level of browsing the doc tree (i.e. not looking at a specific locale)
            if item.code:
              untranslatedhref = item.href + untranslatedhref
              fuzzyhref = item.href + fuzzyhref
        ?>
        <ul>
        <span py:if="item.data.untranslatedsourcewords" py:strip="True">
            <li class="todo"><a href="${l(untranslatedhref)}" py:content="untranslatedwordstext">untranslated words</a></li>
        </span>
        <span py:if="item.data.fuzzysourcewords" py:strip="True">
            <li class="todo"><a href="${l(fuzzyhref)}" py:content="fuzzywordstext">fuzzy words</a></li>
        </span>
        <span py:if="item.data.translatedsourcewords == item.data.totalsourcewords" py:strip="True">
            <li class="complete" py:content="complete">Complete</li>
        </span>
        </ul>
      </td>
      <td class="stats">${item.data.totalsourcewords}</td>
    </span>
  </div>

</include-this>
