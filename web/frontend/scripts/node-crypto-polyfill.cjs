const crypto = require('crypto');

// Node 16 has crypto.randomFillSync, but not crypto.getRandomValues.
if (!globalThis.crypto) {
  globalThis.crypto = {};
}

if (typeof globalThis.crypto.getRandomValues !== 'function') {
  globalThis.crypto.getRandomValues = function getRandomValues(array) {
    if (!ArrayBuffer.isView(array)) {
      throw new TypeError('Expected an array view');
    }
    return crypto.randomFillSync(array);
  };
}


