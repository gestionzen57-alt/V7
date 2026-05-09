@echo off
REM ============================================================
REM PowerFlow V6 - Script de sauvegarde Git ultra-simple
REM Utilisation : double-cliquer sur ce fichier
REM ============================================================

echo.
echo ========================================
echo  PowerFlow V6 - Sauvegarde Git
echo ========================================
echo.

REM Afficher le statut actuel
echo [1/4] Statut actuel du depot...
git status
echo.

REM Ajouter tous les fichiers modifies
echo [2/4] Ajout de tous les fichiers modifies...
git add .
echo.

REM Demander un message de commit (optionnel - sinon utilise un message auto)
set /p commit_msg="Message de commit (appuyez sur Entree pour message auto) : "

if "%commit_msg%"=="" (
    set commit_msg=Checkpoint auto - %date% %time%
)

REM Faire le commit
echo [3/4] Creation du commit...
git commit -m "%commit_msg%"
echo.

REM Pusher vers GitHub
echo [4/4] Envoi vers GitHub...
git push origin main
echo.

REM Confirmation
echo ========================================
echo  Sauvegarde terminee !
echo ========================================
echo.

pause
