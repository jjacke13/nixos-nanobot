const SCHEMA_TELEGRAM = {
  id: "channels",
  titleKey: "section.channels.title",
  descKey: "section.channels.desc",
  stepKey: "stepTelegram",
  fields: [
    {
      key: "channels.telegram.enabled",
      labelKey: "field.tgEnable.label",
      helpKey: "field.tgEnable.help",
      type: "toggle",
    },
    {
      key: "_tg_guide",
      type: "guide",
      titleKey: "tg.guide.title",
      steps: ["tg.guide.step1", "tg.guide.step2", "tg.guide.step3", "tg.guide.step4"],
      showWhen: { key: "channels.telegram.enabled", value: true },
    },
    {
      key: "channels.telegram.allowFrom",
      labelKey: "field.tgUserId.label",
      helpKey: "field.tgUserId.help",
      placeholderKey: "field.tgUserId.placeholder",
      type: "multi-text",
      showWhen: { key: "channels.telegram.enabled", value: true },
    },
    {
      key: "channels.telegram.token",
      labelKey: "field.tgToken.label",
      helpKey: "field.tgToken.help",
      placeholderKey: "field.tgToken.placeholder",
      type: "password",
      showWhen: { key: "channels.telegram.enabled", value: true },
    },
  ],
};
