/**
 * HAR (HTTP Archive) Parser
 *
 * Program of Thoughts Implementation:
 * 1. Parse HAR JSON format
 * 2. Extract user interactions from HTTP requests
 * 3. Infer UI actions from form submissions and navigation
 * 4. Convert to normalized Playwright actions
 * 5. Build test scenario from network activity
 *
 * Uplift Feature: PILLAR 2 - Recording Intelligence (ROI: 9.5/10)
 * Enables: Network-based recording without browser instrumentation
 */

import { Logger } from '../utils/logger';
import { ParsedPlaywrightAction } from './python-parser';

/**
 * HAR format interfaces (subset of the spec)
 */
export interface HARFormat {
  log: {
    version: string;
    creator: {
      name: string;
      version: string;
    };
    browser?: {
      name: string;
      version: string;
    };
    pages?: HARPage[];
    entries: HAREntry[];
  };
}

export interface HARPage {
  id: string;
  startedDateTime: string;
  title: string;
  pageTimings: {
    onContentLoad: number;
    onLoad: number;
  };
}

export interface HAREntry {
  startedDateTime: string;
  time: number;
  request: {
    method: string;
    url: string;
    httpVersion: string;
    headers: Array<{ name: string; value: string }>;
    queryString?: Array<{ name: string; value: string }>;
    postData?: {
      mimeType: string;
      text?: string;
      params?: Array<{ name: string; value: string }>;
    };
  };
  response: {
    status: number;
    statusText: string;
    httpVersion: string;
    headers: Array<{ name: string; value: string }>;
    content: {
      size: number;
      mimeType: string;
      text?: string;
    };
  };
  cache: object;
  timings: object;
}

export interface HARParseResult {
  actions: ParsedPlaywrightAction[];
  metadata: {
    startUrl?: string;
    browser?: string;
    totalRequests: number;
    totalActions: number;
    hasFormSubmissions: boolean;
    hasAjaxCalls: boolean;
  };
  parseErrors: Array<{
    reason: string;
    context?: string;
  }>;
}

/**
 * Main entry point: Parse HAR file
 */
export function parseHARFile(content: string): HARParseResult {
  Logger.info('Parsing HAR (HTTP Archive) file...');

  const actions: ParsedPlaywrightAction[] = [];
  const parseErrors: Array<{ reason: string; context?: string }> = [];

  const metadata = {
    startUrl: undefined as string | undefined,
    browser: undefined as string | undefined,
    totalRequests: 0,
    totalActions: 0,
    hasFormSubmissions: false,
    hasAjaxCalls: false
  };

  try {
    // Parse HAR JSON
    const har: HARFormat = JSON.parse(content);

    if (!har.log || !har.log.entries) {
      throw new Error('Invalid HAR format: missing log.entries');
    }

    metadata.totalRequests = har.log.entries.length;
    metadata.browser = har.log.browser?.name;

    Logger.info(`Found ${har.log.entries.length} HTTP requests`);

    let lineNumber = 0;

    // PoT Step 1: Extract navigation (page loads)
    const navigations = extractNavigations(har.log.entries);
    navigations.forEach(nav => {
      lineNumber++;
      actions.push({
        type: 'goto',
        url: nav.url,
        rawLine: `Navigation to ${nav.url}`,
        lineNumber,
        pageContext: 'page'
      });
    });

    if (navigations.length > 0) {
      metadata.startUrl = navigations[0].url;
    }

    // PoT Step 2: Extract form submissions
    const formSubmissions = extractFormSubmissions(har.log.entries);
    metadata.hasFormSubmissions = formSubmissions.length > 0;

    formSubmissions.forEach(form => {
      // Convert form data to fill + click actions
      form.fields.forEach(field => {
        lineNumber++;
        actions.push({
          type: 'fill',
          locatorType: 'label',
          locatorValue: field.name,
          value: field.value,
          rawLine: `Fill field '${field.name}' with '${field.value}'`,
          lineNumber,
          pageContext: 'page'
        });
      });

      // Add submit action
      lineNumber++;
      actions.push({
        type: 'click',
        locatorType: 'role',
        locatorValue: 'button',
        elementName: 'Submit',
        rawLine: `Submit form to ${form.url}`,
        lineNumber,
        pageContext: 'page'
      });
    });

    // PoT Step 3: Extract AJAX/XHR calls (API interactions)
    const ajaxCalls = extractAjaxCalls(har.log.entries);
    metadata.hasAjaxCalls = ajaxCalls.length > 0;

    // Log AJAX calls for context but don't convert to actions
    // (they're usually triggered by UI interactions)
    if (ajaxCalls.length > 0) {
      Logger.info(`  - Found ${ajaxCalls.length} AJAX/API calls`);
    }

    // PoT Step 4: Extract link clicks from GET requests
    const linkClicks = extractLinkClicks(har.log.entries, navigations);
    linkClicks.forEach(link => {
      lineNumber++;
      actions.push({
        type: 'click',
        locatorType: 'text',
        locatorValue: link.text,
        rawLine: `Click link '${link.text}' → ${link.url}`,
        lineNumber,
        pageContext: 'page'
      });
    });

    metadata.totalActions = actions.length;

    Logger.info(`✓ Extracted ${actions.length} actions from HAR`);
    if (metadata.hasFormSubmissions) Logger.info('  - Contains form submissions');
    if (metadata.hasAjaxCalls) Logger.info('  - Contains AJAX calls');

  } catch (error) {
    Logger.error(`Failed to parse HAR file: ${error instanceof Error ? error.message : String(error)}`);
    parseErrors.push({
      reason: `HAR parsing failed: ${error instanceof Error ? error.message : String(error)}`
    });
  }

  return { actions, metadata, parseErrors };
}

/**
 * Extract navigation events (document loads)
 *
 * PoT:
 * 1. Filter entries with HTML mime type
 * 2. Filter main document requests (not iframes, images, etc.)
 * 3. Return chronological list of page navigations
 */
function extractNavigations(entries: HAREntry[]): Array<{ url: string; timestamp: Date }> {
  const navigations: Array<{ url: string; timestamp: Date }> = [];

  for (const entry of entries) {
    const { request, response } = entry;

    // Check if this is a main document load
    const isDocument = response.content.mimeType.includes('text/html');
    const isMainFrame = !request.url.includes('iframe');
    const isGet = request.method === 'GET';

    if (isDocument && isMainFrame && isGet) {
      // Avoid duplicate navigations to the same URL
      const lastNav = navigations[navigations.length - 1];
      if (!lastNav || lastNav.url !== request.url) {
        navigations.push({
          url: request.url,
          timestamp: new Date(entry.startedDateTime)
        });
      }
    }
  }

  return navigations;
}

/**
 * Extract form submissions (POST requests with form data)
 *
 * PoT:
 * 1. Filter POST requests
 * 2. Extract form-encoded or multipart data
 * 3. Parse field names and values
 * 4. Return structured form data
 */
function extractFormSubmissions(entries: HAREntry[]): Array<{
  url: string;
  fields: Array<{ name: string; value: string }>;
}> {
  const forms: Array<{ url: string; fields: Array<{ name: string; value: string }> }> = [];

  for (const entry of entries) {
    const { request } = entry;

    if (request.method === 'POST' && request.postData) {
      const { mimeType, params, text } = request.postData;

      const fields: Array<{ name: string; value: string }> = [];

      // Extract from params (form-encoded)
      if (params) {
        params.forEach(param => {
          fields.push({ name: param.name, value: param.value });
        });
      }

      // Extract from text (if JSON or URL-encoded)
      if (text && mimeType.includes('application/x-www-form-urlencoded')) {
        const urlParams = new URLSearchParams(text);
        urlParams.forEach((value, name) => {
          fields.push({ name, value });
        });
      }

      if (text && mimeType.includes('application/json')) {
        try {
          const json = JSON.parse(text);
          Object.entries(json).forEach(([name, value]) => {
            fields.push({ name, value: String(value) });
          });
        } catch {
          // Ignore JSON parse errors
        }
      }

      if (fields.length > 0) {
        forms.push({
          url: request.url,
          fields
        });
      }
    }
  }

  return forms;
}

/**
 * Extract AJAX/XHR calls
 *
 * PoT:
 * 1. Filter XHR requests (XMLHttpRequest, fetch)
 * 2. Exclude resource loads (images, CSS, JS)
 * 3. Return API calls
 */
function extractAjaxCalls(entries: HAREntry[]): Array<{
  method: string;
  url: string;
  data?: any;
}> {
  const ajaxCalls: Array<{ method: string; url: string; data?: any }> = [];

  for (const entry of entries) {
    const { request } = entry;

    // Check if XHR/fetch (has XHR header or is JSON/XML)
    const isXHR = request.headers.some(h =>
      h.name.toLowerCase() === 'x-requested-with' && h.value === 'XMLHttpRequest'
    );

    const isJsonOrXml = request.headers.some(h =>
      h.name.toLowerCase() === 'content-type' &&
      (h.value.includes('application/json') || h.value.includes('application/xml'))
    );

    if (isXHR || isJsonOrXml) {
      const call: { method: string; url: string; data?: any } = {
        method: request.method,
        url: request.url
      };

      // Include POST data
      if (request.postData?.text) {
        try {
          call.data = JSON.parse(request.postData.text);
        } catch {
          call.data = request.postData.text;
        }
      }

      ajaxCalls.push(call);
    }
  }

  return ajaxCalls;
}

/**
 * Extract link clicks from GET requests
 *
 * PoT:
 * 1. Find GET requests that aren't initial navigations
 * 2. Infer link text from URL or referer
 * 3. Return click actions
 */
function extractLinkClicks(
  entries: HAREntry[],
  navigations: Array<{ url: string; timestamp: Date }>
): Array<{ text: string; url: string }> {
  const clicks: Array<{ text: string; url: string }> = [];

  const navUrls = new Set(navigations.map(n => n.url));

  for (const entry of entries) {
    const { request, response } = entry;

    // HTML GET requests that aren't first-time navigations
    if (
      request.method === 'GET' &&
      response.content.mimeType.includes('text/html') &&
      !navUrls.has(request.url)
    ) {
      // Infer link text from URL path
      const url = new URL(request.url);
      const pathParts = url.pathname.split('/').filter(p => p);
      const text = pathParts.length > 0 ? pathParts[pathParts.length - 1] : 'Link';

      clicks.push({
        text: text.charAt(0).toUpperCase() + text.slice(1),
        url: request.url
      });
    }
  }

  return clicks;
}

/**
 * Infer test scenario name from HAR data
 */
export function inferScenarioFromHAR(har: HARFormat): string {
  if (har.log.pages && har.log.pages.length > 0) {
    return har.log.pages[0].title || 'User Journey';
  }

  const firstNav = har.log.entries.find(e =>
    e.request.method === 'GET' &&
    e.response.content.mimeType.includes('text/html')
  );

  if (firstNav) {
    const url = new URL(firstNav.request.url);
    const domain = url.hostname.replace('www.', '');
    return `${domain} Journey`;
  }

  return 'User Journey';
}
