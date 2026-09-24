#!/usr/bin/env node
'use strict';

const assert = require('assert');
const {
    DEFAULT_ATLAS_VLM_BASE_URL,
    DEFAULT_ATLAS_VLM_MODEL,
    resolveAtlasVlmConfig,
    validateAtlasVlmConfig,
} = require('./atlas-vlm-config.cjs');

const disabled = resolveAtlasVlmConfig([], {});
assert.deepStrictEqual(disabled, { enabled: false });
assert.strictEqual(validateAtlasVlmConfig(disabled), null);

const missingConfirmation = resolveAtlasVlmConfig(['--atlas-vlm'], {
    ATLASCLOUD_API_KEY: 'test-key',
});
assert.match(validateAtlasVlmConfig(missingConfirmation), /paid/);

const missingKey = resolveAtlasVlmConfig(
    ['--atlas-vlm', '--confirm-paid-atlas'],
    {},
);
assert.match(validateAtlasVlmConfig(missingKey), /ATLASCLOUD_API_KEY/);

const configured = resolveAtlasVlmConfig(
    ['--atlas-vlm', '--confirm-paid-atlas'],
    { ATLASCLOUD_API_KEY: 'test-key' },
);
assert.strictEqual(configured.baseUrl, DEFAULT_ATLAS_VLM_BASE_URL);
assert.strictEqual(configured.model, DEFAULT_ATLAS_VLM_MODEL);
assert.strictEqual(validateAtlasVlmConfig(configured), null);

const overriddenModel = resolveAtlasVlmConfig(
    ['--atlas-vlm', '--confirm-paid-atlas'],
    {
        ATLAS_CLOUD_API_KEY: 'alias-key',
        ATLASCLOUD_VLM_MODEL: 'example/vision-model',
    },
);
assert.strictEqual(overriddenModel.apiKey, 'alias-key');
assert.strictEqual(overriddenModel.model, 'example/vision-model');

console.log('Atlas VLM configuration: 5 tests passed');
