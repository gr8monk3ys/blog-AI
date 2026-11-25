# Changelog

## [0.2.2](https://github.com/gr8monk3ys/blog-AI/compare/v0.2.1...v0.2.2) (2026-11-25)


### Bug Fixes

* **api:** keep API keys and conversations in Postgres when DATABASE_URL is set ([#257](https://github.com/gr8monk3ys/blog-AI/issues/257)) ([375b463](https://github.com/gr8monk3ys/blog-AI/commit/375b46362762543d5698afc45db6e788dba9e922))
* keep query strings out of Vercel Analytics ([#244](https://github.com/gr8monk3ys/blog-AI/issues/244)) ([f02cfc3](https://github.com/gr8monk3ys/blog-AI/commit/f02cfc38b0470b238fd0425e35a524695f7001cc))
* **pricing:** gate research copy on capability and show checkout unavailable ([#256](https://github.com/gr8monk3ys/blog-AI/issues/256)) ([02c4982](https://github.com/gr8monk3ys/blog-AI/commit/02c4982c18190736c996ccd362de7a973e50bd45))
* **seo:** list only public pages in the sitemap ([#248](https://github.com/gr8monk3ys/blog-AI/issues/248)) ([fceffe1](https://github.com/gr8monk3ys/blog-AI/commit/fceffe1ac846220b8689321ef9b9db8d2b15381c))
* site-wide crash with Clerk 7, Stripe webhooks failing, usage never recorded ([#247](https://github.com/gr8monk3ys/blog-AI/issues/247)) ([b77626d](https://github.com/gr8monk3ys/blog-AI/commit/b77626deadf6eebdcc67af7d1db1afde19274137))
* **web:** send public pages as finished HTML, not behind the workspace spinner ([#254](https://github.com/gr8monk3ys/blog-AI/issues/254)) ([ac60231](https://github.com/gr8monk3ys/blog-AI/commit/ac60231f92e0eb648282c7f8cfb7ac2992ecd870))
* **web:** stop console errors on /pricing and /tools for signed-out visitors ([#251](https://github.com/gr8monk3ys/blog-AI/issues/251)) ([c411829](https://github.com/gr8monk3ys/blog-AI/commit/c41182994e775f4e59aa905a13b0b7ccd849c7d5))

## [0.2.1](https://github.com/gr8monk3ys/blog-AI/compare/v0.2.0...v0.2.1) (2026-11-10)


### Bug Fixes

* **deps:** bump certifi to 2026.10.19 in apps/api ([#231](https://github.com/gr8monk3ys/blog-AI/issues/231)) ([6fa5963](https://github.com/gr8monk3ys/blog-AI/commit/6fa5963c72da015bad18c6210ba37e7982da0b5b))

## [0.2.0](https://github.com/gr8monk3ys/blog-AI/compare/v0.1.0...v0.2.0) (2026-10-21)


### Features

* **design:** Manuscript notebook tokens, fonts, primitives, brand and enforcement ([#227](https://github.com/gr8monk3ys/blog-AI/issues/227)) ([760fb92](https://github.com/gr8monk3ys/blog-AI/commit/760fb92ff717ba9dae6d31e9b9586c9a69c3fc57))
* **design:** marketing and public pages on the notebook ([#229](https://github.com/gr8monk3ys/blog-AI/issues/229)) ([9ef27b7](https://github.com/gr8monk3ys/blog-AI/commit/9ef27b788be6d3c1d740a26afb5541b362c82af3))


### Bug Fixes

* truthful deployment docs, feature flags, web health endpoint and env audit ([#226](https://github.com/gr8monk3ys/blog-AI/issues/226)) ([f7fdad0](https://github.com/gr8monk3ys/blog-AI/commit/f7fdad0dda55f582e0ed00d9f33100a7f52e7629))

## 0.1.0 (2026-10-13)


### Features

* **research:** add SerpBase as an optional Google SERP provider ([#172](https://github.com/gr8monk3ys/blog-AI/issues/172)) ([b8c1faf](https://github.com/gr8monk3ys/blog-AI/commit/b8c1faff81cb022983cb24718857d6a783ded0d8))


### Build System

* **release:** start versioning at 0.1.0, not 1.0.0 ([#224](https://github.com/gr8monk3ys/blog-AI/issues/224)) ([63748ff](https://github.com/gr8monk3ys/blog-AI/commit/63748ff22b515f61a76b52968d1dc3d54c6a947f))
