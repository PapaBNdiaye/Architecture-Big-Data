@echo off
echo Auto-restart producteur météo (Ctrl+C pour quitter)
:loop
python kafka_producer.py --continuous --interval 5
echo Process terminé (code %errorlevel%). Redémarrage dans 5s...
timeout /t 5 >nul
goto loop
