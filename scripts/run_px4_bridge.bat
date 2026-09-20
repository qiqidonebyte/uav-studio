@echo off
cd /d %~dp0\..
if "%PX4_CONNECTION%"=="" set PX4_CONNECTION=udpin:0.0.0.0:14540
python -m backend.px4_service
