# -*- coding: utf-8 -*-
r"""와쿠와쿠 7 배포 묶음 — dist/WakuWaku7_KR_<VER>/ : 트랙 1 xdelta + xdelta.exe + readme.txt(CP949) + 한글패치_적용.bat(CP949) + zip
  (소드 & 소서리 tools/make_dist.py 를 옮김, 2026-10-27) 바뀌는 트랙: 트랙 01 만(02~45 = 오디오, cue 그대로).
  검증: 원본 트랙 1 → xdelta 적용 → md5 = 빌드(dist/build) 트랙 1 md5.
  python tools/make_dist.py   (먼저 tools/wak_build.py · gfx_moves.py --build · gfx_err.py --build · discbuild.py --write)
"""
import hashlib, os, shutil, subprocess, sys, zipfile
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)

VER = 'v0.9'
XDELTA = r'C:\claude\utils\xdelta.exe'
ROM = 'Waku Waku 7 (Japan)'
SRC = os.path.join(r'D:\hospi\My Documents\한글패치\SS\ss', ROM)
OUT = os.path.join(ROOT, 'dist', 'build', ROM)
NAME = 'WakuWaku7_KR_' + VER
TITLE = '와쿠와쿠 7 (Waku Waku 7, 세가 새턴 일본판) 한글 패치 ' + VER


def md5(p):
    h = hashlib.md5()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 22), b''):
            h.update(b)
    return h.hexdigest().upper()


README = """{title}
{line}

45개의 트랙으로 이루어진 {rom} 의
트랙 01번에 패치하시면 됩니다.

원본md5 : {o}
패치md5 : {d}

입니다.


[ 적용 방법 ]

  1) 원본 트랙 1 파일을 이 폴더에 복사
       "{bin}"
  2) 한글패치_적용.bat 실행 → 이름 끝에 [KR] 이 붙은 파일이 만들어집니다
  3) 만든 파일 이름을 원본 트랙 01 이름으로 바꿔 넣고, 트랙 02~45(오디오)와 cue 는 원본 그대로 쓰세요

  직접 적용:
    xdelta.exe -d -s "원본 트랙 1" "{patch}" "결과 파일"
  (Delta Patcher 같은 xdelta3 GUI 도구로 적용해도 됩니다. 원본이 다르면 xdelta 가 적용을 거부합니다.)


[ 바뀌는 것 ]

  - 승부 전·승리·패배 대사 말풍선 전체
  - 오프닝 스토리 문구·노래 가사·캐릭터 소개·조작 설명·거대 보스전 대사
  - 캐릭터별 엔딩 대사
  - 캐릭터 선택 화면 기술표(기술 이름)
  - 확장 RAM 카트리지 경고·백업 RAM 용량 부족 안내 화면
  - 타이틀 로고 "두근두근7"(그림 글자), 위 영문 "DUGUN DUGUN SEVEN"


[ 알려진 점 ]

  - 음성·노래는 원본 일본어 그대로입니다.
  - 확장 RAM 카트리지(1MB)가 필요합니다(원본과 같음).
  - 옵션 LANGUAGE 에서 ENGLISH·SPANISH 를 고르면 오프닝 스토리·캐릭터 소개가 깨집니다
    (한글 글이 영어·스페인어 글 자리까지 씁니다). JAPANESE 로 두세요.
  - 글자 칸이 모자라 엔딩 대사 일부는 짧은 말로 옮겼습니다.
  - 로딩 화면(WAKUWAKU NEXT MATCH·FIGHT! 등)의 영문 그림 글자는 원본 그대로입니다.
  - 엔딩 스태프 롤은 원본 그대로입니다.
"""

BAT = r"""@echo off
chcp 949 >nul
set "XD=%~dp0xdelta.exe"
if not exist "%~dp0{bin}" (
  echo   [오류] 원본 트랙 1 파일을 이 폴더에 넣어 주세요 - readme 참고.
  pause & exit /b 1
)
"%XD%" -d -f -s "%~dp0{bin}" "%~dp0{patch}" "%~dp0{kbin}"
if errorlevel 1 (
  echo   [오류] 패치 실패 - 원본이 다를 수 있습니다 - readme 의 원본md5 확인.
  pause & exit /b 1
)
echo   완료: "{kbin}"
pause
"""


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    d = os.path.join(ROOT, 'dist', NAME)
    if os.path.isdir(d):
        shutil.rmtree(d)
    os.makedirs(d)
    b = '%s (Track 01).bin' % ROM
    src, out = os.path.join(SRC, b), os.path.join(OUT, b)
    patch = NAME + '_Track01.xdelta'; pp = os.path.join(d, patch)
    subprocess.run([XDELTA, '-e', '-9', '-B', '536870912', '-f', '-s', src, out, pp], check=True)
    chk = os.path.join(d, '_check.bin')
    subprocess.run([XDELTA, '-d', '-f', '-s', src, pp, chk], check=True)
    o, want, got = md5(src), md5(out), md5(chk)
    os.remove(chk)
    assert got == want, ('패치 적용 결과가 빌드와 다름', got, want)
    print('트랙 01 원본md5 %s → 패치md5 %s · %s %d B' % (o, want, patch, os.path.getsize(pp)))
    shutil.copy2(XDELTA, os.path.join(d, 'xdelta.exe'))
    kbin = '%s (Track 01) [KR].bin' % ROM
    readme = README.format(title=TITLE, line='=' * 60, rom=ROM, o=o, d=want, bin=b, patch=patch)
    open(os.path.join(d, 'readme.txt'), 'wb').write(readme.replace('\n', '\r\n').encode('cp949'))
    open(os.path.join(d, '한글패치_적용.bat'), 'wb').write(BAT.format(bin=b, patch=patch, kbin=kbin).replace('\n', '\r\n').encode('cp949'))
    z = os.path.join(ROOT, 'dist', NAME + '.zip')
    with zipfile.ZipFile(z, 'w', zipfile.ZIP_DEFLATED) as zf:
        for f in sorted(os.listdir(d)):
            zf.write(os.path.join(d, f), NAME + '/' + f)
    print('✅', d)
    for f in sorted(os.listdir(d)):
        print('  %-56s %12d' % (f, os.path.getsize(os.path.join(d, f))))
    print('  zip %s %d B · md5 %s' % (os.path.basename(z), os.path.getsize(z), md5(z)))


if __name__ == '__main__':
    main()
