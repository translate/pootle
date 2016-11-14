/*
 * Copyright (C) Pootle contributors.
 *
 * This file is a part of the Pootle project. It is distributed under the GPL3
 * or later license. See the LICENSE file for a copy of the license and the
 * AUTHORS file for copyright and authorship information.
 */

import EditorContainer from '../containers/EditorContainer';
import SuggestionValue from '../components/SuggestionValue';
import UnitSource from '../components/UnitSource';
import ViewUnit from '../components/ViewUnit';


const FormatAdaptor = {
  editorComponent: EditorContainer,
  suggestionValueComponent: SuggestionValue,
  unitSourceComponent: UnitSource,
  viewUnitComponent: ViewUnit,
};


export default FormatAdaptor;
