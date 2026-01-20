@echo off
rem этот .bat файл запускает конвертацию с выбором профиля

:menu
cls
echo.
echo =========================================
echo   ВЫБЕРИТЕ ПРОФИЛЬ ДЛЯ КОНВЕРТАЦИИ
echo =========================================
echo.
echo   1. Itel it2163R      (160x128, 3GP/MPEG4)
echo   2. BQ 3590 Step XXL+ (480x320, 3GP/MPEG4)
echo.
echo   0. Выход
echo.
echo =========================================
echo.

set /p choice="Введите номер (1, 2 или 0) и нажмите Enter: "

if "%choice%"=="1" goto run_itel
if "%choice%"=="2" goto run_bq
if "%choice%"=="0" goto :eof

echo.
echo Неверный выбор! Пожалуйста, введите 1, 2 или 0.
pause
goto menu

:run_itel
cls
echo.
echo --- Запускается конвертация для Itel it2163R ---
echo.
python convertproj.py itel_it2163r
goto end

:run_bq
cls
echo.
echo --- Запускается конвертация для BQ 3590 ---
echo.
python convertproj.py bq_3590
goto end

:end
echo.
echo.
echo =========================================
echo   РАБОТА ЗАВЕРШЕНА
echo =========================================
echo.
pause