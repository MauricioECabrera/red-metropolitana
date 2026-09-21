<#
=====================================================================
  dbt.ps1  ·  Ejecuta dbt con las variables de entorno del proyecto
  Proyecto 1  ·  Ciencia de Datos  ·  Red Metropolitana

  Carga el archivo .env de la raiz del repositorio en el proceso y
  ejecuta dbt desde la carpeta dbt con los argumentos recibidos.

  Ejecutar desde cualquier carpeta del repositorio:
    .\scripts\dbt.ps1 build
    .\scripts\dbt.ps1 build --select path:models/gold
=====================================================================
#>

$raiz = Split-Path -Parent $PSScriptRoot
$archivoEnv = Join-Path $raiz ".env"

if (-not (Test-Path $archivoEnv)) {
    Write-Host "No existe el archivo .env en la raiz del repositorio. Copiar .env.example a .env y completarlo." -ForegroundColor Red
    exit 1
}

Get-Content $archivoEnv | ForEach-Object {
    $linea = $_.Trim()
    if ($linea -and -not $linea.StartsWith("#") -and $linea.Contains("=")) {
        $partes = $linea.Split("=", 2)
        [Environment]::SetEnvironmentVariable($partes[0].Trim(), $partes[1].Trim(), "Process")
    }
}

Push-Location (Join-Path $raiz "dbt")
try {
    dbt @args
    $codigo = $LASTEXITCODE
}
finally {
    Pop-Location
}
exit $codigo