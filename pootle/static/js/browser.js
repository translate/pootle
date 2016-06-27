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


const sel = {
  breadcrumbs: '.js-breadcrumb',
  navigation: '#js-select-navigation',
  language: '#js-select-language',
  project: '#js-select-project',
  resource: '#js-select-resource',
};


const actionMap = {
  browse: '',
  translate: 'translate',
  'admin-permissions': 'admin/permissions',
  'admin-characters': 'admin/characters',
  'admin-languages': 'admin/languages',
  'admin-terminology': 'terminology',
};


/* Navigates to `languageCode`, `projectCode`, `resource` while
 * retaining the current context when applicable */
function navigateTo(languageCode, projectCode, resource) {
  const curProject = $(sel.project).data('initial-code');
  const curLanguage = $(sel.language).data('initial-code');
  const $resource = $(sel.resource);
  const curResource = $resource.length ? $resource.data('initial-code')
                                                  .replace('ctx-', '') : '';
  const langChanged = languageCode !== curLanguage;
  const projChanged = projectCode !== curProject;
  const resChanged = resource !== curResource;
  const hasChanged = langChanged || projChanged || resChanged;

  if (!hasChanged) {
    return;
  }

  const actionKey = $(sel.navigation).val();
  const action = actionMap[actionKey];
  const inAdmin = (actionKey.indexOf('admin-') !== -1 &&
                   ((curLanguage === '' && curProject !== '') ||
                    (curLanguage !== '' && curProject === '')));

  let newLanguageCode = languageCode;
  if (!newLanguageCode && !inAdmin) {
    newLanguageCode = 'projects';
  }
  let newResource = resource;
  if (projectCode === '' || projChanged) {
    newResource = '';
  }

  const parts = ['', newLanguageCode, projectCode, action, newResource];
  const urlParts = parts.filter((p, i) => i === 0 || p !== '');

  if (!newResource) {
    urlParts.push('');
  }

  let newUrl = l(urlParts.join('/'));

  const PTL = window.PTL || {};
  if (PTL.hasOwnProperty('editor')) {
    const hash = utils.getHash()
          .replace(/&?unit=\d+/, '')
          .replace(/&?offset=\d+/, '');
    if (hash !== '') {
      newUrl = [newUrl, hash].join('#');
    }
  }

  let changed;
  if (projChanged) {
    changed = 'project';
  } else if (langChanged) {
    changed = 'language';
  } else {
    changed = 'resource';
  }

  cookie('user-choice', changed, { path: '/' });

  // Remember the latest language the user switched to
  if (langChanged) {
    cookie('pootle-language', newLanguageCode, { path: '/' });
  }

  window.location.href = newUrl;
}


function handleNavDropDownSelectClick() {
  const $select = $(this);
  const $opt = $select.find('option:selected');
  const href = $opt.data('href');

  if (href) {
    const openInNewTab = $opt.data('new-tab');

    if (openInNewTab) {
      window.open(href, '_blank');
      // Reset drop-down to its original value
      $select.select2('val', $select.data('initial-code'));
    } else {
      window.location.href = href;
    }

    return false;
  }

  const langCode = $(sel.language).val();
  const projectCode = $(sel.project).val();
  const $resource = $(sel.resource);
  const resource = $resource.length ? $resource.val().replace('ctx-', '') : '';
  navigateTo(langCode, projectCode, resource);
  return true;
}


function handleBeforeNavDropDownResourceSelect(e) {
  const resource = e.val ? e.val.replace('ctx-', '') : '';
  if (resource !== '') {
    return;
  }

  e.preventDefault();
  const $select = $(this);
  if ($select.val() === '') {
    $select.select2('close');
  } else {
    $select.select2('val', '');
    $select.select2('close');
    handleNavDropDownSelectClick();
  }
}


function makeNavDropdown(selector, opts, handleSelectClick, handleBeforeSelect) {
  const defaults = {
    allowClear: true,
    dropdownAutoWidth: true,
    dropdownCssClass: 'breadcrumb-dropdown',
    width: 'off',
  };
  const options = $.extend({}, defaults, opts);

  return utils.makeSelectableInput(
    selector,
    options,
    handleSelectClick,
    handleBeforeSelect
  );
}


/* Recalculate breadcrumb geometry on window resize */
function fixResourcePathBreadcrumbGeometry() {
  const $resourceDropdown = $('#s2id_js-select-resource');
  // on some pages there's no resource dropdown
  if ($resourceDropdown.length) {
    const sideMargin = $('#s2id_js-select-navigation').position().left;

    const maxHeaderWidth = $('#header-meta').outerWidth() - sideMargin;
    const resourceDropdownLeft = $resourceDropdown.position().left;

    const maxWidth = maxHeaderWidth - resourceDropdownLeft;
    $resourceDropdown.css('max-width', maxWidth);
  }
}


function fixDropdowns() {
  // We can't use `e.persisted` here. See bug 2949 for reference
  const selectors = [sel.navigation, sel.language, sel.project, sel.resource];
  for (let i = 0; i < selectors.length; i++) {
    const $el = $(selectors[i]);
    $el.select2('val', $el.data('initial-code'));
  }
  fixResourcePathBreadcrumbGeometry();
  $(sel.breadcrumbs).css('visibility', 'visible');
}


function formatResult(text, term) {
  const match = text.toUpperCase().indexOf(term.toUpperCase());
  if (match < 0) {
    return _.escape(text);
  }

  const tl = term.length;
  return [
    _.escape(text.substring(0, match)),
    '<span class="select2-match">',
    _.escape(text.substring(match, match + tl)),
    '</span>',
    _.escape(text.substring(match + tl, text.length)),
  ].join('');
}

function formatResource(path, container, query) {
  const $el = $(path.element);
  if ($el.prop('disabled')) {
    return '';
  }

  const t = `/${path.text.trim()}`;
  return [
    '<span class="', $el.data('icon'), '">',
    '<i class="icon-', $el.data('icon'), '"></i>',
    '<span class="text">', formatResult(t, query.term), '</span>',
    '</span>',
  ].join('');
}


function formatProject(path, container, query) {
  const state = path.element[0].dataset.state;

  return `<span class="text project-${state}">${formatResult(path.text, query.term)}</span>`;
}


function formatLanguage(path, container, query) {
  return formatResult(path.text, query.term);
}


function removeCtxEntries(results, container, query) {
  if (query.term) {
    return results.filter((result) => result.id.slice(0, 4) !== 'ctx-');
  }
  return results;
}


const browser = {

  init() {
    $(window).on('pageshow', fixDropdowns);

    makeNavDropdown(sel.navigation, {
      minimumResultsForSearch: -1,
    }, handleNavDropDownSelectClick);
    makeNavDropdown(sel.language, {
      placeholder: gettext('All Languages'),
      formatResult: formatLanguage,
    }, handleNavDropDownSelectClick);
    makeNavDropdown(sel.project, {
      placeholder: gettext('All Projects'),
      formatResult: formatProject,
    }, handleNavDropDownSelectClick);
    makeNavDropdown(sel.resource, {
      placeholder: gettext('Entire Project'),
      formatResult: formatResource,
      sortResults: removeCtxEntries,
    }, handleNavDropDownSelectClick, handleBeforeNavDropDownResourceSelect);

    /* Adjust breadcrumb layout on window resize */
    $(window).on('resize', () => {
      fixResourcePathBreadcrumbGeometry();
    });
  },

};


export default browser;
