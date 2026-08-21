'use strict';

const DEFAULT_ATLAS_VLM_BASE_URL = 'https://api.atlascloud.ai/v1';
const DEFAULT_ATLAS_VLM_MODEL = 'qwen/qwen3-vl-235b-a22b-thinking';

function resolveAtlasVlmConfig(args = [], env = {}) {
    const enabled = args.includes('--atlas-vlm');
    if (!enabled) return { enabled: false };

    return {
        enabled: true,
        confirmed: args.includes('--confirm-paid-atlas'),
        baseUrl: DEFAULT_ATLAS_VLM_BASE_URL,
        apiKey: env.ATLASCLOUD_API_KEY || env.ATLAS_CLOUD_API_KEY || '',
        model: env.ATLASCLOUD_VLM_MODEL || DEFAULT_ATLAS_VLM_MODEL,
    };
}

function validateAtlasVlmConfig(config) {
    if (!config.enabled) return null;
    if (!config.confirmed) {
        return 'Atlas VLM requests are paid. Review the live model price, then add --confirm-paid-atlas.';
    }
    if (!config.apiKey) {
        return 'Set ATLASCLOUD_API_KEY (or ATLAS_CLOUD_API_KEY) before using --atlas-vlm.';
    }
    return null;
}

module.exports = {
    DEFAULT_ATLAS_VLM_BASE_URL,
    DEFAULT_ATLAS_VLM_MODEL,
    resolveAtlasVlmConfig,
    validateAtlasVlmConfig,
};
