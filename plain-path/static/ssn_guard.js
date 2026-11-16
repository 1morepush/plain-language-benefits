/*
 * ssn_guard.js — the browser copy of the SSN blocker.
 *
 * It warns the user right away, before anything leaves their device.
 * The server runs the same check again (ssn_guard.py), and that one is the real block.
 * The pattern below must stay identical to SSN_PATTERN in ssn_guard.py.
 * (A unit test fails if the two copies ever differ.)
 */
const SSN_PATTERN = "(?<![0-9])[0-9]{3}[-. –—]?[0-9]{2}[-. –—]?[0-9]{4}(?![0-9])";
const SSN_REGEX = new RegExp(SSN_PATTERN);

function looksLikeSsn(text) {
  return SSN_REGEX.test(text || "");
}
