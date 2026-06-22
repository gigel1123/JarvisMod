@echo off
setlocal enabledelayedexpansion
title JarvisMod Environment Setup
winget list
winget install Python.Python.3.12
winget install Ollama.Ollama
winget install Git.Git
ollama pull qwen2.5-vl:3b

call JarvisMod_Setup
exit