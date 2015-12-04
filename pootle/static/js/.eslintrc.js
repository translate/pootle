module.exports = {
  env: {
    browser: true,
    es6: true,
  },
  ecmaFeatures: {
    jsx: true,
    modules: true,
  },
  globals: {
    gettext: false,
    ngettext: false,
    interpolate: false,
    l: false,
    PTL: false,
  },
  plugins: [
    'react',
  ],
  rules: {
    'comma-dangle': [2, 'always-multiline'],
    'comma-spacing': [2, {'before': false, 'after': true}],
    'indent': [2, 2, { "SwitchCase": 1, "VariableDeclarator": 1 }],
    'one-var': [2, 'never'],
    'quotes': [2, 'single', 'avoid-escape'],
    'semi': [2, 'always'],
    'space-before-function-paren': [2, { 'anonymous': 'always', 'named': 'never' }],
    'strict': [2, 'never'],
  },
};
