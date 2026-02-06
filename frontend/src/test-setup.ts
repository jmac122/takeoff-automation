import '@testing-library/jest-dom';

// jsdom doesn't implement scrollIntoView
if (typeof Element.prototype.scrollIntoView !== 'function') {
  Element.prototype.scrollIntoView = () => {};
}
