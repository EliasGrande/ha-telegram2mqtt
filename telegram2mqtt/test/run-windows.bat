@echo off
setlocal

cd /d "%~dp0"

set "COMPOSE_FILE=%~dp0docker-compose.yml"

where docker >nul 2>nul
if errorlevel 1 (
    echo Docker Desktop is not installed or not in PATH.
    echo Please install Docker Desktop and start it.
    pause
    exit /b 1
)

where docker-compose >nul 2>nul
if not errorlevel 1 (
    set "COMPOSE_CMD=docker-compose"
) else (
    docker compose version >nul 2>nul
    if not errorlevel 1 (
        set "COMPOSE_CMD=docker compose"
    ) else (
        echo Docker Compose is not available.
        echo Please ensure Docker Desktop is installed and Compose is enabled.
        pause
        exit /b 1
    )
)

echo Building and running the Docker container using Docker Compose...
%COMPOSE_CMD% -f "%COMPOSE_FILE%" up --build --abort-on-container-exit --exit-code-from verifier
set "TEST_EXIT_CODE=%ERRORLEVEL%"

%COMPOSE_CMD% -f "%COMPOSE_FILE%" down --rmi all

echo.
echo Docker Compose exit code: %TEST_EXIT_CODE%
if not "%TEST_EXIT_CODE%"=="0" (
    echo TEST RESULT: FAIL
    exit /b %TEST_EXIT_CODE%
) else (
    echo TEST RESULT: PASS
    exit /b 0
)
