# Crimson_Old

Esta pasta guarda a versão **legado (monolítica)** do Crimson, a V.3.0.1, em que todo o programa ficava em um único arquivo, o `Crimson.py` (4085 linhas).

## Por que ela existe

A partir da V.4.0.0 o Crimson foi reestruturado em módulos (pacote `crimson/`), com buildsystem próprio (pyproject.toml e Meson). Esta cópia foi mantida apenas como **referência de estudo** e para comparar o antes e o depois da modularização.

## Importante

- Esta pasta **não faz parte do build**: nem o Meson nem o pyproject.toml instalam o que está aqui.
- Não receberá novas funcionalidades nem correções.
- Para usar o Crimson, utilize a versão atual na raiz do repositório.

---

This folder keeps the **legacy (monolithic)** version of Crimson, V.3.0.1, where the whole program lived in a single file, `Crimson.py` (4085 lines).

Since V.4.0.0 Crimson has been restructured into modules (the `crimson/` package) with its own build system (pyproject.toml and Meson). This copy is kept only as a **study reference** and to compare the before and after of the modularization. It is **not part of the build** and will not receive new features or fixes.