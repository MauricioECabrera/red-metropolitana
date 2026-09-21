# Modelo dimensional Gold

Generado por `scripts/exportar_modelo.py` desde el warehouse y los tests de dbt. Las llaves primarias salen de los tests `unique` y las foráneas de los tests `relationships`.

```mermaid
erDiagram
    dim_zona ||--o{ dim_estacion : "zona_key"
    dim_zona ||--o{ dim_persona : "zona_residencia_key"
    dim_estacion ||--o{ fct_abordaje : "estacion_key"
    dim_fecha ||--o{ fct_abordaje : "fecha_key"
    dim_hora ||--o{ fct_abordaje : "hora_key"
    dim_modo ||--o{ fct_abordaje : "modo_key"
    dim_persona ||--o{ fct_abordaje : "persona_sk"
    dim_zona ||--o{ fct_abordaje : "zona_key"
    dim_fecha ||--o{ fct_estado_padron_diario : "fecha_key"
    dim_persona ||--o{ fct_estado_padron_diario : "persona_sk"
    dim_zona ||--o{ fct_estado_padron_diario : "zona_residencia_key"
    dim_estacion ||--o{ fct_trayecto_od : "estacion_destino_key"
    dim_estacion ||--o{ fct_trayecto_od : "estacion_origen_key"
    dim_zona ||--o{ fct_trayecto_od : "zona_destino_key"
    dim_zona ||--o{ fct_trayecto_od : "zona_origen_key"

    dim_estacion {
        VARCHAR estacion_key PK
        INTEGER modo_key
        VARCHAR modo_codigo
        VARCHAR codigo_origen
        VARCHAR nombre_punto
        VARCHAR linea_ruta
        VARCHAR zona_key FK
        DOUBLE latitud
        DOUBLE longitud
        DOUBLE km_trazado
    }

    dim_fecha {
        INTEGER fecha_key PK
        DATE fecha
        BIGINT anio
        BIGINT mes
        VARCHAR nombre_mes
        BIGINT dia
        BIGINT dia_semana_num
        VARCHAR nombre_dia
        BIGINT semana_iso
        BOOLEAN es_dia_habil
        BOOLEAN es_fin_de_semana
    }

    dim_hora {
        INTEGER hora_key PK
        VARCHAR hora_etiqueta
        VARCHAR franja_horaria
        BOOLEAN es_franja_pico
    }

    dim_modo {
        INTEGER modo_key PK
        VARCHAR modo_codigo
        VARCHAR modo_nombre
        VARCHAR unidad_registro
        VARCHAR formato_origen
    }

    dim_persona {
        VARCHAR persona_sk PK
        VARCHAR tipo_identidad
        BOOLEAN en_padron
        VARCHAR estado_padron
        VARCHAR perfil_vigente
        VARCHAR zona_residencia_key FK
        VARCHAR formato_llave_padron
        BIGINT versiones_padron
    }

    dim_zona {
        VARCHAR zona_key PK
        VARCHAR zona_nombre
        VARCHAR tipo_division
        VARCHAR municipio
        BIGINT puntos_de_abordaje
        BIGINT modos_con_servicio
        VARCHAR modos_lista
        BOOLEAN tiene_servicio
    }

    fct_abordaje {
        VARCHAR abordaje_id PK
        VARCHAR persona_sk FK
        INTEGER modo_key FK
        VARCHAR estacion_key FK
        VARCHAR zona_key FK
        INTEGER fecha_key FK
        INTEGER hora_key FK
        VARCHAR tipo_abordaje
        BOOLEAN es_hora_pico
        INTEGER cantidad_abordajes
        DECIMAL monto_q
    }

    fct_estado_padron_diario {
        INTEGER fecha_key PK, FK
        VARCHAR persona_sk PK, FK
        VARCHAR zona_residencia_key FK
        VARCHAR perfil
        VARCHAR estado
        INTEGER cantidad_personas
        INTEGER tarjetas_activas
    }

    fct_trayecto_od {
        VARCHAR trayecto_id PK
        VARCHAR persona_sk
        VARCHAR estacion_origen_key FK
        VARCHAR estacion_destino_key FK
        VARCHAR zona_origen_key FK
        VARCHAR zona_destino_key FK
        INTEGER fecha_key
        INTEGER hora_key
        BOOLEAN es_hora_pico
        INTEGER cantidad_trayectos
        BIGINT duracion_s
        DOUBLE distancia_km
        DECIMAL monto_q
    }
```
