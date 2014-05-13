(function ($) {

  window.PTL = window.PTL || {};

  var sel = {
    breadcrumbs: '.js-breadcrumb',
    navigation: '#js-select-navigation',
    language: '#js-select-language',
    project: '#js-select-project',
    goal: '#js-select-goal',
    resource: '#js-select-resource'
  };

  var actionMap = {
    'overview': '',
    'translate': 'translate',
    'news': 'notices',
    'admin-permissions': 'admin/permissions',
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

    return PTL.utils.makeSelectableInput(selector, opts,
      function (e) {
        var $opt = $(e.target).find('option:selected'),
            href = $opt.data('href');

        if (href) {
          window.location.href = href;
          return false;
        }

        var langCode = $(sel.language).val(),
            projectCode = $(sel.project).val(),
            $goal = $(sel.goal),
            goalSlug = $goal.length ? $goal.val(): '';
            $resource = $(sel.resource),
            resource = $resource.length ? $resource.val()
                                                   .replace('ctx-', '')
                                        : '';
        PTL.browser.navigateTo(langCode, projectCode, goalSlug, resource);
      }
    );
  };

  var fixDropdowns = function (e) {
    // We can't use `e.persisted` here. See bug 2949 for reference
    var selectors = [sel.navigation, sel.language, sel.project, sel.goal,
          sel.resource
        ];
    for (var i=0; i<selectors.length; i++) {
      var $el = $(selectors[i]),
          initial = $el.data('initial-code');
      $el.select2('val', initial);
    }
    $(sel.breadcrumbs).css('visibility', 'visible');
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
        '<span class="text">', t, '</span>',
      '</span>'
    ].join('');
  };


  PTL.browser = {

    init: function () {
      makeNavDropdown(sel.navigation, {
        minimumResultsForSearch: -1
      });
      makeNavDropdown(sel.language, {
        placeholder: gettext("All Languages")
      });
      makeNavDropdown(sel.project, {
        placeholder: gettext("All Projects")
      });
      makeNavDropdown(sel.goal, {
        placeholder: gettext("All Goals")
      });
      makeNavDropdown(sel.resource, {
        placeholder: gettext("Entire Project"),
        formatResult: formatResource
      });
    },

    /* Navigates to `languageCode`, `projectCode`, `resource` while
     * retaining the current context when applicable */
    navigateTo: function (languageCode, projectCode, goalSlug, resource) {
      var curProject = $(sel.project).data('initial-code'),
          curLanguage = $(sel.language).data('initial-code'),
          $goal = $(sel.goal),
          curGoal = $goal.length ? $goal.data('initial-code') : '',
          $resource = $(sel.resource),
          curResource = $resource.length ? $resource.data('initial-code')
                                                    .replace('ctx-', '') : '',
          langChanged = languageCode !== curLanguage,
          projChanged = projectCode !== curProject,
          goalChanged = goalSlug !== curGoal,
          resChanged = resource !== curResource,
          hasChanged = langChanged || projChanged || goalChanged || resChanged;

      if (!hasChanged) {
        return;
      }

      if (!languageCode || !projectCode) {
        goalSlug = '';
      }

      if (!languageCode) {
        languageCode = 'projects';
      }
      if (projectCode === '' || projChanged) {
        resource = '';
      }

      var action = actionMap[$(sel.navigation).val()],
          goalPart = goalSlug ? ['goals', goalSlug, 'real-path'].join('/') : '',
          parts = ['', languageCode, projectCode, action, goalPart, resource],
          urlParts = parts.filter(function (p, i) {
            return i === 0 || p !== '';
          });

      if (!resource) {
        urlParts.push('');
      }

      newUrl = l(urlParts.join('/'));

      if (PTL.hasOwnProperty('editor')) {
        var hash = window.location.hash.replace(/(\#|&)unit=\d+/, '');
        newUrl = [newUrl, hash].join('');
      }

      var changed = projChanged ? 'project' :
                    langChanged ? 'language' : 'resource';
      $.cookie('user-choice', changed, {path: '/'});

      // Remember the latest language the user switched to
      if (langChanged) {
        $.cookie('pootle-language', languageCode, {path: '/'});
      }

      window.location.href = newUrl;
    }

  };

  $(window).on('pageshow', fixDropdowns);

}(jQuery));


$(function () {
  PTL.browser.init();
});
