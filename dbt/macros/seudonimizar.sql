{#
=====================================================================
  seudonimizar  ·  Identificador opaco y estable de una persona
  Proyecto 1  ·  Ciencia de Datos  ·  Red Metropolitana

  SHA-256 de la sal secreta concatenada con la llave de persona.
  La sal vive en la variable de entorno SEUDONIMIZACION_SAL, nunca
  en el repositorio. Sin sal valida la compilacion se detiene.
=====================================================================
#}

{% macro seudonimizar(columna) -%}
    {%- set sal = env_var('SEUDONIMIZACION_SAL', '') -%}
    {%- if execute and (sal | length < 32 or sal.startswith('cambiar')) -%}
        {{ exceptions.raise_compiler_error("SEUDONIMIZACION_SAL no esta definida o es la de ejemplo. Configurarla en .env y ejecutar dbt con scripts/dbt.ps1") }}
    {%- endif -%}
    left(sha256('{{ sal }}' || {{ columna }}), 16)
{%- endmacro %}