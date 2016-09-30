/*
 * Copyright (C) Pootle contributors.
 *
 * This file is a part of the Pootle project. It is distributed under the GPL3
 * or later license. See the LICENSE file for a copy of the license and the
 * AUTHORS file for copyright and authorship information.
 */

import assign from 'object-assign';

import { FTLASTParser, FTLASTSerializer, getPluralForms } from 'l20n';


class L20nEditorError extends Error {
  constructor(message, id) {
    super();
    this.name = 'L20nEditorError';
    this.message = message;
    this.id = id;
  }
}


function getTextElementL20nEntity(value) {
  const textElementResource = FTLASTParser.parseResource('unit = value');
  textElementResource[0].body[0].value.elements[0].value = value;

  return textElementResource[0].body[0];
}


function parseL20nValue(value) {
  try {
    const unitEntity = FTLASTParser.parseResource(`unit = ${value}`)[0].body[0];
    return { unitEntity, error: null };
  } catch (e) {
    if (e.name === 'L10nError') {
      return { unitEntity: null, error: e };
    }
    throw e;
  }
}


function setL20nPlurals(data) {
  const value = data.unitEntity.value;
  const hasL20nPlurals = (value !== undefined &&
                          value.elements.length === 1 &&
                          value.elements[0].type === 'Placeable' &&
                          value.elements[0].expressions[0].type === 'SelectExpression' &&
                          value.elements[0].expressions[0].expression.callee.name === 'PLURAL');
  assign(data, { hasL20nPlurals });
  if (hasL20nPlurals) {
    const unitValues = [];
    const pluralForms = [];
    const variants = data.unitEntity.value.elements[0].expressions[0].variants;
    for (let i = 0; i < variants.length; i++) {
      unitValues.push(variants[i].value.source);
      let key = FTLASTSerializer.dumpExpression(variants[i].key);
      if (variants[i].default) {
        key = `${key}, default`;
      }
      pluralForms.push(key);
    }
    assign(data, { unitValues, pluralForms });
  }
  return hasL20nPlurals;
}


function setSimpleValue(data) {
  const value = data.unitEntity.value;
  const hasSimpleValue = (value !== undefined &&
                    value.elements.length === 1 &&
                    value.elements[0].type === 'TextElement');

  if (hasSimpleValue) {
    assign(data, { unitValues: [value.source] });
  }
  assign(data, { hasSimpleValue });
  return hasSimpleValue;
}


export function getL20nData(values, nplurals) {
  if (nplurals !== undefined && nplurals !== 1 || values.length !== 1 || values[0] === '') {
    return { isEmpty: true };
  }
  const result = parseL20nValue(values[0]);
  if (result.error !== null) {
    return result;
  }

  if (setL20nPlurals(result)) {
    return result;
  }

  setSimpleValue(result);

  return result;
}


export function dumpL20nPlurals(values, l20nUnitEntity) {
  const variants = l20nUnitEntity.value.elements[0].expressions[0].variants;

  if (values.every(value => value === '')) {
    return '';
  } else if (values.some(value => value === '')) {
    throw new L20nEditorError('All plural forms should be filled.');
  }
  for (let i = 0; i < values.length; i++) {
    const textElementEntity = getTextElementL20nEntity(values[i]);
    variants[i].value = textElementEntity.value;
  }

  try {
    return [FTLASTSerializer.dumpPattern(l20nUnitEntity.value)];
  } catch (e) {
    throw new L20nEditorError(e.message);
  }
}


export function dumpL20nValue(value) {
  const l20nUnitEntity = getTextElementL20nEntity(value);

  try {
    return FTLASTSerializer.dumpPattern(l20nUnitEntity.value);
  } catch (e) {
    throw new L20nEditorError(e.message);
  }
}


export function getL20nEmptyPluralsEntity(localeCode) {
  const pluralForms = getPluralForms(localeCode);
  const pluralFormsPattern = pluralForms.map((x) => `[${x}] val`).join('\n');
  const unit = `unit = { PLURAL($num) -> \n ${pluralFormsPattern} \n}`;
  const unitEntity = FTLASTParser.parseResource(unit)[0].body[0];
  return { unitEntity, pluralForms };
}


export { L20nEditorError as L20nEditorError };
