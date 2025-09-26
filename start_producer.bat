@echo off
REM Lance le producteur en mode continu (intervalle 5s)
python kafka_producer.py --continuous --interval 5
