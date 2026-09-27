# Public LLM Provider descriptor

This example is the smallest public LLM Provider plugin. It describes one
reviewed HTTPS OpenAI-compatible endpoint and a bounded static model list;
AutoTask creates the workspace Gateway Provider during installation. The
plugin does not run code, discover models, set prices, or carry an API key.

The endpoint in `manifest.template.json` is a documentation placeholder. A
submission must replace it with the provider's real HTTPS endpoint and declare
the matching `network:<host>` permission. Never put an API key, OAuth secret,
proxy URL, `models_url`, or arbitrary headers in the manifest.

```bash
python3 prepare.py --author-id 123
python3 -m unittest -v test_manifest.py
```

Installers enter the API key once in the platform's plugin configuration form.
The reviewed base URL and protocol are read-only, and the model selector only
contains the models declared in the manifest. Reconfiguring an installation
with an empty key keeps its existing encrypted key.

The public authoring contract and rejection rules are documented at
[`docs.autotask.run`](https://docs.autotask.run/).
