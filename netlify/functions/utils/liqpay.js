// LiqPay crypto helpers — sign & verify
const crypto = require('crypto');

function sign(privateKey, data) {
  return crypto
    .createHash('sha1')
    .update(privateKey + data + privateKey)
    .digest('base64');
}

function encode(obj) {
  return Buffer.from(JSON.stringify(obj)).toString('base64');
}

function decode(data) {
  return JSON.parse(Buffer.from(data, 'base64').toString('utf8'));
}

function verify(privateKey, data, signature) {
  return sign(privateKey, data) === signature;
}

module.exports = { sign, encode, decode, verify };
