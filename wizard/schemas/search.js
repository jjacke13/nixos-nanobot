const SCHEMA_SEARCH = {
  id: "search",
  titleKey: "section.search.title",
  descKey: "section.search.desc",
  stepKey: "stepSearch",
  fields: [
    {
      key: "search.provider",
      labelKey: "field.searchProvider.label",
      helpKey: "field.searchProvider.help",
      type: "select",
      options: [
        { value: "tavily", labelKey: "opt.tavily" },
        { value: "searxng", labelKey: "opt.searxng" },
      ],
    },
    {
      key: "search.apiKey",
      labelKey: "field.searchApiKey.label",
      helpKey: "field.searchApiKey.help",
      placeholderKey: "field.searchApiKey.placeholder",
      type: "password",
      hideWhen: { key: "search.provider", value: "searxng" },
    },
    {
      key: "search.baseUrl",
      labelKey: "field.searchBaseUrl.label",
      helpKey: "field.searchBaseUrl.help",
      type: "text",
      placeholder: "https://api.tavily.com/search",
    },
    {
      key: "search.maxResults",
      labelKey: "field.searchMaxResults.label",
      helpKey: "field.searchMaxResults.help",
      type: "number",
      placeholder: "5",
    },
  ],
};
