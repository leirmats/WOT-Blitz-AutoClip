@echo off
setlocal
py -3 -m pip install -r requirements.txt || goto fail
if not exist build_tools mkdir build_tools
if not exist build_tools\ffmpeg.exe (
  powershell -NoProfile -ExecutionPolicy Bypass -Command "$u='https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip'; Invoke-WebRequest $u -OutFile build_tools\ffmpeg.zip; Expand-Archive -Force build_tools\ffmpeg.zip build_tools\ffmpeg_extract; $f=Get-ChildItem -Recurse build_tools\ffmpeg_extract -Filter ffmpeg.exe | Select-Object -First 1; Copy-Item $f.FullName build_tools\ffmpeg.exe" || goto fail
)
py -3 -m PyInstaller --noconfirm --clean --onefile --windowed --name WoT_Blitz_AutoClip --collect-all tkinterdnd2 --add-binary "build_tools\ffmpeg.exe;." app.py || goto fail
echo BUILD COMPLETE: dist\WoT_Blitz_AutoClip.exe
exit /b 0
:fail
echo BUILD FAILED
exit /b 1
