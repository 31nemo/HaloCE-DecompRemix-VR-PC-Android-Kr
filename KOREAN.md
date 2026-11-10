# Halo CE Decomp Remix — 한국판 디스크 지원 (비공식 한국어 패치)

[moistman42069/HaloCE-DecompRemix-VR-PC-Android](https://github.com/moistman42069/HaloCE-DecompRemix-VR-PC-Android)
**v1.0.41** 에 한국판 Xbox 디스크 *Halo - Jeonjaengui Seomak (Korea) (En,Ko)* (헤일로: 전쟁의 서막) 지원을 더한 버전입니다.
한국판 디스크의 **한국어 음성과 한국어 글자(HUD·자막·미션 목표 등)** 로 플레이할 수 있습니다.

원작자와 무관한 비공식 수정본이며, Microsoft와도 관계가 없습니다. 게임 파일은 들어 있지 않습니다. 각자 가진 디스크 이미지를 씁니다.

## 설치

[Releases](../../releases) 에서 기기에 맞는 APK를 받습니다.

| 파일 | 기기 |
|---|---|
| `HaloCE-Quest-1.0.41-kr1.apk` | Meta Quest (VR) |
| `HaloCE-Android-1.0.41-kr1.apk` | 안드로이드 폰·태블릿 |

1. **원본 앱이 설치되어 있으면 먼저 지웁니다.** 서명이 달라서 덮어쓸 수 없습니다.
   지우면 그 앱에 가져온 맵과 세이브도 지워지니 필요하면 먼저 백업하세요.
2. APK를 설치합니다 (Quest: SideQuest 또는 `adb install`).
3. 실행해서 **한국판 디스크 이미지(ISO/XISO)** 를 고릅니다.
   맵을 꺼낸 뒤 "Korean fonts: … (N of M MB)" 단계가 몇 분 동안 이어집니다. 끝까지 기다리세요.

미국판 디스크도 그대로 쓸 수 있습니다 (원본과 같이 동작).

## 한국어로 나오는 것 / 영어로 남는 것

- 한국어: 음성, HUD 안내, 자막, 미션 목표 등 **게임 맵에서 나오는 글자와 소리**, 원래 Xbox 화면의 그림 제목
- 영어: 메인 메뉴·LOAD LEVEL·설정처럼 **이 포트가 새로 만든 메뉴** (원본 포트의 영어 문구)
- 글자는 맵의 원래 그림 폰트로 그립니다 (고해상도 글자 기본 끔). 그래서 원본보다 조금 흐릴 수 있습니다.

## 바뀐 점 (원본 v1.0.41 대비, 2026-11-11)

| 문제 | 원인 | 수정 |
|---|---|---|
| 한국판 디스크를 거부 | 맵 빌드 `01.12.09.0135` 가 지원 목록에 없음 | 런처 `MapInfo.java`, 엔진 `cache_files.c` 빌드 표에 추가 (엔진 표에서는 `01.08.15.1749` 자리를 대신함) |
| 영어 맵(`maps/`)을 가져옴 | 디스크에 `maps/` 와 `maps_kr/` 가 같이 있음 | `XisoExtractor.java`: `maps_kr` 우선 |
| "a structure bsp is damaged" 로 멈춤 | 한국판 실행 파일의 태그 캐시가 더 큼 (`0x167D000`) | `TAG_CACHE_SIZE` `0x1600000` → `0x1680000` |
| 시작하자마자 꺼짐 (`cseries.c #279`) | 늘린 태그 캐시가 게임 상태 메모리와 겹침 | `HALO_PORT_GAME_STATE_BASE_ADDRESS` `0x81A00000` → `0x81B00000` |
| 글자가 하나도 안 나옴 | 한국판 폰트(`ui\large_ui`, `ui\small_ui`)는 문자표가 비어 있고, 한글 코드 = 글자 번호 + `0xA1` (한국판 실행 파일이 계산으로 찾던 방식) | 디스크를 가져올 때 `KoreanFonts.java` 가 그 폰트에 문자표를 만들어 넣음 |
| 한글이 엉뚱한 글자로 나옴 | 고해상도 글자(Overpass TTF)가 한국판 코드를 라틴 문자로 그림 | `display.high_res_text` → `display.hires_text_kr`, 기본값 `false` |

소스 변경은 이 저장소의 커밋 하나에 모두 들어 있습니다 (`git diff v1.0.41`).

### 릴리스 APK를 만든 방법

릴리스 APK는 원작자가 배포한 공식 v1.0.41 APK (SHA-256 `8f7a10dd…` Quest, `b4ffaeec…` Android) 에
위 변경과 같은 내용을 적용해 만들었습니다: `tools/korean/hc_build.py --korean-maps`
(엔진 `halo_guest.elf` 의 해당 상수·문자열, 런처 smali, `KoreanFonts` 를 dex로 추가, 재서명).
같은 변경을 소스로 적용한 것이 이 커밋이며 (`tools/korean/hc_source.py`), 이 소스로 빌드해도 같은 동작입니다.

## 라이선스

원본과 같이 **AGPL-3.0-or-later** ([LICENSE](LICENSE)). 원본의 [CREDITS](CREDITS.md), [THIRD-PARTY-NOTICES](THIRD-PARTY-NOTICES.txt) 를 따릅니다.
이 라이선스는 Halo 자체(게임, 맵, 상표 등 Microsoft 소유물)에 대한 권리를 주지 않습니다.
이 수정판으로 다른 사람과 네트워크 게임을 호스팅하는 경우 AGPL 13조에 따라 이 저장소가 그 소스입니다.

---

**English:** an unofficial fork of HaloCE Decomp Remix v1.0.41 that supports the Korean Xbox disc
(*Halo - Jeonjaengui Seomak*, maps_kr, cache build 01.12.09.0135) with its Korean voice and text: build
recognition, a larger tag cache (0x1680000) with the game state moved to 0x81B00000, maps_kr import, character
tables for the Korean fonts (Hangul code = glyph index + 0xA1) and high-res text off by default. All source
changes are in one commit on top of v1.0.41. Not affiliated with the original author or Microsoft; no game
files included. AGPL-3.0-or-later.
