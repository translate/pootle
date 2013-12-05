(function ($) {

  window.PTL = window.PTL || {};

  PTL.browser = {

    init: function () {
      PTL.utils.makeSelectableInput('#js-select-language',
        {
          allowClear: true,
          dropdownAutoWidth: true,
          dropdownCssClass: 'breadcrumb-dropdown',
          placeholder: gettext("All Languages"),
          width: 'off'
        },
        function (e) {
          var langCode = $(this).val(),
              projectCode = $('#js-select-project').val();
              resource = $('#js-select-resource').val() || '';
          PTL.browser.navigateTo(langCode, projectCode, resource);
      });
      PTL.utils.makeSelectableInput('#js-select-project',
        {
          allowClear: true,
          dropdownAutoWidth: true,
          dropdownCssClass: 'breadcrumb-dropdown',
          placeholder: gettext("All Projects"),
          width: 'off'
        },
        function (e) {
          var projectCode = $(this).val(),
              langCode = $('#js-select-language').val(),
              resource = $('#js-select-resource').val() || '';
          PTL.browser.navigateTo(langCode, projectCode, resource);
      });
      PTL.utils.makeSelectableInput('#js-select-resource',
        {
          allowClear: true,
          dropdownAutoWidth: true,
          dropdownCssClass: 'breadcrumb-dropdown',
          placeholder: gettext("All Resources"),
          width: 'off'
        },
        function (e) {
          var resource = $(this).val(),
              projectCode = $('#js-select-project').val();
              langCode = $('#js-select-language').val();
          PTL.browser.navigateTo(langCode, projectCode, resource);
        }
      );
    },

    /* Navigates to `languageCode`, `projectCode`, `resource` while
     * retaining the current context when applicable */
    navigateTo: function (languageCode, projectCode, resource) {
      var curProject = $('#js-select-project').data('initial-code'),
          curLanguage = $('#js-select-language').data('initial-code'),
          curResource = $('#js-select-resource').data('initial-code'),
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


$(function ($) {
  PTL.browser.init();

  $('.js-breadcrumb').css('visibility', 'visible');
});
