(function ($) {

  window.PTL = window.PTL || {};

  var sel = {
    breadcrumbs: '.js-breadcrumb',
    language: '#js-select-language',
    project: '#js-select-project',
    resource: '#js-select-resource'
  };

  var makeNavDropdown = function (selector, placeholder, formatFunc) {
    var opts = {
        allowClear: true,
        dropdownAutoWidth: true,
        dropdownCssClass: 'breadcrumb-dropdown',
        placeholder: placeholder,
        width: 'off'
      };
    formatFunc && (opts.formatResult = formatFunc);

    return PTL.utils.makeSelectableInput(selector, opts,
      function (e) {
        var langCode = $(sel.language).val(),
            projectCode = $(sel.project).val();
            resource = $(sel.resource).val() || '';
        PTL.browser.navigateTo(langCode, projectCode, resource);
      }
    );
  };

  var fixDropdowns = function (e) {
    // We can't use `e.persisted` here. See bug 2949 for reference
    var selectors = [sel.language, sel.project, sel.resource];
    for (var i=0; i<selectors.length; i++) {
      var $el = $(selectors[i]),
          initial = $el.data('initial-code');
      $el.select2('val', initial);
    }
  };

  PTL.browser = {

    init: function () {
      makeNavDropdown(sel.language, gettext("All Languages"));
      makeNavDropdown(sel.project, gettext("All Projects"));
      makeNavDropdown(sel.resource, gettext("Entire Project"),
        function format(path, container, query) {
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
        }
      );

      $(sel.breadcrumbs).css('visibility', 'visible');
    },

    /* Navigates to `languageCode`, `projectCode`, `resource` while
     * retaining the current context when applicable */
    navigateTo: function (languageCode, projectCode, resource) {
      var curProject = $(sel.project).data('initial-code'),
          curLanguage = $(sel.language).data('initial-code'),
          curResource = $(sel.resource).data('initial-code'),
          curUrl = window.location.toString(),
          newUrl = curUrl,
          langChanged = languageCode !== curLanguage,
          projChanged = projectCode !== curProject,
          resChanged = resource !== curResource,
          hasChanged = langChanged || projChanged || resChanged;

      if (!hasChanged) {
        return;
      }

      /* FIXME: this is more than messy; we need to implement something
       * healthier for humanity
       */
      if (languageCode === '' && projectCode === '') {
        newUrl = l('/projects/');
      } else if (languageCode === '' && projectCode !== '') {
        if (resChanged) {
          newUrl = l(['', 'projects', projectCode, resource].join('/'));
        } else {
          newUrl = l(['', 'projects', projectCode].join('/'));
        }
      } else if (languageCode !== '' && projectCode === '') {
        newUrl = l(['', languageCode].join('/'));
      } else if (languageCode !== '' && projectCode !== '') {
        if (projChanged) {
          newUrl = l(['', languageCode, projectCode].join('/'));
        } else if (langChanged) {
          if (curLanguage === '') {
            newUrl = curUrl.replace('projects/' + curProject,
                                    languageCode + '/' + curProject);
          } else {
            newUrl = curUrl.replace(curLanguage + '/' + curProject,
                                    languageCode + '/' + curProject)
                           .replace(/(\#|&)unit=\d+/, '');
          }
        } else if (resChanged) {
          if (curResource) {
            newUrl = curUrl.replace(curResource, resource);
          } else {
            var pattern = [
              '(', curLanguage, '/', curProject, '/', '([^/]+/)?)', curResource
            ].join(''),
                regex = new RegExp(pattern);

            newUrl = newUrl.replace(regex, ['$1', resource].join(''));
          }
          newUrl = newUrl.replace(/(\#|&)unit=\d+/, '');
        }
        var changed = projChanged ? 'project' : 'language';
        $.cookie('user-choice', changed, {path: '/'});
      }

      window.location.href = newUrl;
    }

  };

  $(window).on('pageshow', fixDropdowns);

}(jQuery));


$(function () {
  PTL.browser.init();
});
