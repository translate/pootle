/*
 * Copyright (C) Pootle contributors.
 *
 * This file is a part of the Pootle project. It is distributed under the GPL3
 * or later license. See the LICENSE file for a copy of the license and the
 * AUTHORS file for copyright and authorship information.
 */

import $ from 'jquery';
import 'jquery-select2';
import _ from 'underscore';

import cookie from 'utils/cookie';

import utils from './utils';


var sel = {
  breadcrumbs: '.js-breadcrumb',
  navigation: '#js-select-navigation',
  language: '#js-select-language',
  project: '#js-select-project',
  resource: '#js-select-resource'
};


var actionMap = {
  'browse': '',
  'translate': 'translate',
  'admin-permissions': 'admin/permissions',
  'admin-characters': 'admin/characters',
  'admin-languages': 'admin/languages',
  'admin-terminology': 'terminology',
};


var makeNavDropdown = function (selector, opts) {
  var defaults = {
      allowClear: true,
      dropdownAutoWidth: true,
      dropdownCssClass: 'breadcrumb-dropdown',
      width: 'off'
    },
    opts = $.extend({}, defaults, opts);

  return utils.makeSelectableInput(selector, opts,
    function (e) {
      var $select = $(this),
          $opt = $select.find('option:selected'),
          href = $opt.data('href'),
          openInNewTab;

      if (href) {
        openInNewTab = $opt.data('new-tab');

        if (openInNewTab) {
          window.open(href, '_blank');
          // Reset drop-down to its original value
          $select.select2('val', $select.data('initial-code'));
        } else {
          window.location.href = href;
        }

        return false;
      }

      var langCode = $(sel.language).val(),
          projectCode = $(sel.project).val(),
          $resource = $(sel.resource),
          resource = $resource.length ? $resource.val()
                                                 .replace('ctx-', '')
                                      : '';
      browser.navigateTo(langCode, projectCode, resource);
    }
  );
};


var fixDropdowns = function (e) {
  // We can't use `e.persisted` here. See bug 2949 for reference
  var selectors = [sel.navigation, sel.language, sel.project, sel.resource];
  for (var i=0; i<selectors.length; i++) {
    var $el = $(selectors[i]),
        initial = $el.data('initial-code');
    $el.select2('val', initial);
  }
  fixResourcePathBreadcrumbGeometry();
  $(sel.breadcrumbs).css('visibility', 'visible');
};


/* Recalculate breadcrumb geometry on window resize */
var fixResourcePathBreadcrumbGeometry = function () {
  var $projectDropdown = $('#s2id_js-select-project');
  var $resourceDropdown = $('#s2id_js-select-resource');
  // on some pages there's no resource dropdown
  if ($resourceDropdown.length) {
    var sideMargin = $('#s2id_js-select-navigation').position().left;

    var maxHeaderWidth = $('#header-meta').outerWidth() - sideMargin;
    var resourceDropdownLeft = $resourceDropdown.position().left;

    var maxWidth = maxHeaderWidth - resourceDropdownLeft;
    $resourceDropdown.css("max-width", maxWidth);
  }
};


var formatResource = function (path, container, query) {
  var $el = $(path.element);

  if ($el.prop('disabled')) {
    return '';
  }

  var t = '/' + path.text.trim();

  if (query.term !== '') {
    var escaped_term = query.term.replace(
          /[\-\[\]\/\{\}\(\)\*\+\?\.\\\^\$\|]/g,
          '\\$&'
        ),
        regex = new RegExp(escaped_term, 'gi');
    t = t.replace(regex, '<span class="select2-match">$&</span>');
  }

  return [
    '<span class="', $el.data('icon'), '">',
    '<i class="icon-', $el.data('icon'), '"></i>',
    '<span class="text">', _.escape(t), '</span>',
    '</span>',
  ].join('');
};


function formatProject(path, container, query) {
  const state = path.element[0].dataset.state;
  return `<span class="text project-${state}">${_.escape(path.text)}</span>`;
};


var removeCtxEntries = function (results, container, query) {
  if (query.term) {
    return _.filter(results, function (result) {
      return result.id.slice(0, 4) !== 'ctx-';
    });
  }
  return results;
};


var browser = {

  init: function () {
    $(window).on('pageshow', fixDropdowns);

    makeNavDropdown(sel.navigation, {
      minimumResultsForSearch: -1
    });
    makeNavDropdown(sel.language, {
      placeholder: gettext("All Languages")
    });
    makeNavDropdown(sel.project, {
      placeholder: gettext("All Projects"),
      formatResult: formatProject,
    });
    makeNavDropdown(sel.resource, {
      placeholder: gettext("Entire Project"),
      formatResult: formatResource,
      sortResults: removeCtxEntries
    });

    /* Adjust breadcrumb layout on window resize */
    $(window).on("resize", function (e) {
      fixResourcePathBreadcrumbGeometry();
    });
  },

  /* Navigates to `languageCode`, `projectCode`, `resource` while
   * retaining the current context when applicable */
  navigateTo: function (languageCode, projectCode, resource) {
    var curProject = $(sel.project).data('initial-code'),
        curLanguage = $(sel.language).data('initial-code'),
        $resource = $(sel.resource),
        curResource = $resource.length ? $resource.data('initial-code')
                                                  .replace('ctx-', '') : '',
        langChanged = languageCode !== curLanguage,
        projChanged = projectCode !== curProject,
        resChanged = resource !== curResource,
        hasChanged = langChanged || projChanged || resChanged;

    if (!hasChanged) {
      return;
    }

    var actionKey = $(sel.navigation).val(),
        action = actionMap[actionKey],
        inAdmin = (actionKey.indexOf('admin-') !== -1 &&
                   ((curLanguage === '' && curProject !== '') ||
                    (curLanguage !== '' && curProject === '')));

    if (!languageCode && !inAdmin) {
      languageCode = 'projects';
    }
    if (projectCode === '' || projChanged) {
      resource = '';
    }

    var parts = ['', languageCode, projectCode, action, resource],
        urlParts = parts.filter(function (p, i) {
          return i === 0 || p !== '';
        }),
        newUrl;

    if (!resource) {
      urlParts.push('');
    }

    newUrl = l(urlParts.join('/'));

    var PTL = window.PTL || {};
    if (PTL.hasOwnProperty('editor')) {
      var hash = utils.getHash().replace(/&?unit=\d+/, '');
      if (hash !== '') {
        newUrl = [newUrl, hash].join('#');
      }
    }

    var changed = projChanged ? 'project' :
                  langChanged ? 'language' : 'resource';
    cookie('user-choice', changed, { path: '/' });

    // Remember the latest language the user switched to
    if (langChanged) {
      cookie('pootle-language', languageCode, { path: '/' });
    }

    window.location.href = newUrl;
  }

};


export default browser;
