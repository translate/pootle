/*
 * Copyright (C) Pootle contributors.
 *
 * This file is a part of the Pootle project. It is distributed under the GPL3
 * or later license. See the LICENSE file for a copy of the license and the
 * AUTHORS file for copyright and authorship information.
 */

import { FTLASTParser, FTLASTSerializer, getPluralForms } from 'l20n';


export function getL20nPlurals(values, nplurals) {
  if (nplurals !== 1 || values.length !== 1) {
    return false;
  }
  const unitEntity = FTLASTParser.parseResource('unit = ' + values[0])[0].body[0];
  const value = unitEntity.value;
  const hasL20nPlurals = (value !== undefined &&
                          value.elements.length === 1 &&
                          value.elements[0].type === 'Placeable' &&
                          value.elements[0].expressions[0].type === 'SelectExpression' &&
                          value.elements[0].expressions[0].expression.callee.name === 'PLURAL');
  if (hasL20nPlurals) {
    const unitValues = [];
    const pluralForms = [];
    const variants = unitEntity.value.elements[0].expressions[0].variants;
    for (let i in variants) {
      unitValues.push(FTLASTSerializer.dumpPattern(variants[i].value));
      pluralForms.push(FTLASTSerializer.dumpKeyword(variants[i].key))
    }
    return {unitValues, pluralForms, unitEntity};
  }
  return false;
}


export function dumpL20nPlurals(values, l20nUnitEntity) {
  const variants = l20nUnitEntity.value.elements[0].expressions[0].variants;
  for (let i in values) {
    const value = values[i];
    const pfEntity = FTLASTParser.parseResource('unit = ' + value);
    variants[i].value = pfEntity[0].body[0].value;
  }
  return [FTLASTSerializer.dumpPattern(l20nUnitEntity.value)];
}


export function getL20nEmptyPluralsEntity(localeCode) {
  const pluralForms = getPluralForms(localeCode);
  const pluralFormsPattern = pluralForms.map((x) => `[${x}] val`).join('\n');
  const unit = `unit = { PLURAL($num) -> \n ${pluralFormsPattern} \n}`;
  const unitEntity = FTLASTParser.parseResource(unit)[0].body[0];
  return { unitEntity, length: pluralForms.length };
}
