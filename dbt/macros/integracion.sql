{#
=====================================================================
  integracion  ·  Registro de fuentes integradas a la red
  Proyecto 1  ·  Ciencia de Datos  ·  Red Metropolitana

  Unico punto donde se declara que una fuente esta integrada.
  fct_abordaje, la tabla de features, la cuarentena y los tests de
  completitud leen estas listas.

  Para integrar una fuente se agrega una linea a cada lista.
=====================================================================
#}

{% macro fuentes_abordaje() -%}
    {{ return([
        'slv_mr_abordajes',
    ]) }}
{%- endmacro %}

{% macro fuentes_cuarentena() -%}
    {{ return([
        'mr_cuarentena',
    ]) }}
{%- endmacro %}