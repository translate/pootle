(function ($) {

  window.PTL = window.PTL || {};

  var sel = {
    breadcrumbs: '.js-breadcrumb',
    language: '#js-select-language',
    project: '#js-select-project',
    resource: '#js-select-resource'
  };

  var makeNavDropdown = function (selector, placeholder) {
   return PTL.utils.makeSelectableInput(selector,
      {
        allowClear: true,
        dropdownAutoWidth: true,
        dropdownCssClass: 'breadcrumb-dropdown',
        placeholder: placeholder,
        width: 'off'
      },
      function (e) {
        var langCode = $(sel.language).val(),
            projectCode = $(sel.project).val();
            resource = $(sel.resource).val() || '';
        PTL.browser.navigateTo(langCode, projectCode, resource);
      }
    );
  };

  PTL.browser = {

    init: function () {
      makeNavDropdown(sel.language, gettext("All Languages"));
      makeNavDropdown(sel.project, gettext("All Projects"));
      makeNavDropdown(sel.resource, gettext("All Resources"));

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

      if (languageCode === '' && projectCode === '') {
        newUrl = l('/projects/');
      } else if (languageCode === '' && projectCode !== '') {
        newUrl = l(['', 'projects', projectCode, resource].join('/'));
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

}(jQuery));


$(function () {
  PTL.browser.init();
});
