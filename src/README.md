# src

Vanilla TS + D3 (D-011). 상태는 `state/store.ts`의 단일 저장소다. D3 그리기는 `vis/`에 두며, 경계 검사(`scripts/checks/boundaries.mjs`)가 `vis/`에서 프레임워크나 상태를 가져오지 못하게 막는다. `vis/glyphs.generated.ts`는 `docs/specs/glyph_registry.json`에서 생성한다. 현재 상태는 [PROTOTYPE_STATUS](../docs/development/PROTOTYPE_STATUS.md)에 있다.
