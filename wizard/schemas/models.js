const SCHEMA_MODELS = {
  id: "models",
  titleKey: "section.models.title",
  descKey: "section.models.desc",
  stepKey: "stepModels",
  fields: [
    {
      key: "provider",
      labelKey: "field.provider.label",
      helpKey: "field.provider.help",
      type: "select",
      options: [
        { value: "ppq", labelKey: "opt.ppq" },
        { value: "openrouter", labelKey: "opt.openrouter" },
        { value: "openai", labelKey: "opt.openai" },
        { value: "anthropic", labelKey: "opt.anthropic" },
        { value: "gemini", labelKey: "opt.gemini" },
        { value: "custom", labelKey: "opt.custom" },
      ],
    },
    {
      key: "apiBase",
      labelKey: "field.baseUrl.label",
      helpKey: "field.baseUrl.help",
      type: "text",
      placeholder: "https://api.example.com/v1",
      showWhen: { key: "provider", value: "custom" },
      providerDefaults: {
        ppq: "https://api.ppq.ai",
        openrouter: "https://openrouter.ai/api/v1",
        openai: "",
        anthropic: "",
        gemini: "https://generativelanguage.googleapis.com/v1beta/openai",
        custom: "",
      },
    },
    {
      key: "apiKey",
      labelKey: "field.apiKey.label",
      helpKey: "field.apiKey.help",
      placeholderKey: "field.apiKey.placeholder",
      type: "password",
      hideWhen: { key: "provider", value: "ppq" },
    },
    {
      key: "model",
      labelKey: "field.model.label",
      helpKey: "field.model.help",
      type: "model-select",
      fallbackModels: {
        ppq: [
          { id: "gemini-2.5-flash", name: "Gemini 2.5 Flash", descKey: "model.fast" },
          { id: "gemini-2.5-pro", name: "Gemini 2.5 Pro", descKey: "model.capable" },
          { id: "claude-sonnet-4-5", name: "Claude Sonnet 4.5", descKey: "model.balanced" },
          { id: "gpt-4.1", name: "GPT-4.1", descKey: "model.latest" },
        ],
        openrouter: [
          { id: "google/gemini-2.5-flash", name: "Gemini 2.5 Flash", descKey: "model.fast" },
          { id: "anthropic/claude-sonnet-4-5", name: "Claude Sonnet 4.5", descKey: "model.balanced" },
          { id: "openai/gpt-4.1", name: "GPT-4.1", descKey: "model.latest" },
        ],
        openai: [
          { id: "gpt-4.1", name: "GPT-4.1", descKey: "model.most-capable" },
          { id: "gpt-4.1-mini", name: "GPT-4.1 Mini", descKey: "model.cheaper" },
        ],
        anthropic: [
          { id: "claude-sonnet-4-5", name: "Claude Sonnet 4.5", descKey: "model.balanced" },
          { id: "claude-opus-4-5", name: "Claude Opus 4.5", descKey: "model.most-capable" },
        ],
        gemini: [
          { id: "gemini-2.5-flash", name: "Gemini 2.5 Flash", descKey: "model.fast" },
          { id: "gemini-2.5-pro", name: "Gemini 2.5 Pro", descKey: "model.capable" },
        ],
      },
    },
    {
      key: "modelString",
      labelKey: "field.modelString.label",
      helpKey: "field.modelString.help",
      type: "auto",
    },
  ],
};
