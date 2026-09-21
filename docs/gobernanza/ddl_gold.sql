-- ==================================================================
--  ddl_gold.sql  ·  DDL del modelo dimensional Gold
--  Proyecto 1  ·  Ciencia de Datos  ·  Red Metropolitana
--  Generado por scripts/exportar_modelo.py desde el warehouse y
--  los tests unique y relationships de dbt.
-- ==================================================================

create table gold.dim_estacion (
    estacion_key                VARCHAR,
    modo_key                    INTEGER,
    modo_codigo                 VARCHAR,
    codigo_origen               VARCHAR,
    nombre_punto                VARCHAR,
    linea_ruta                  VARCHAR,
    zona_key                    VARCHAR,
    latitud                     DOUBLE,
    longitud                    DOUBLE,
    km_trazado                  DOUBLE,
    primary key (estacion_key),
    foreign key (zona_key) references gold.dim_zona (zona_key)
);

create table gold.dim_fecha (
    fecha_key                   INTEGER,
    fecha                       DATE,
    anio                        BIGINT,
    mes                         BIGINT,
    nombre_mes                  VARCHAR,
    dia                         BIGINT,
    dia_semana_num              BIGINT,
    nombre_dia                  VARCHAR,
    semana_iso                  BIGINT,
    es_dia_habil                BOOLEAN,
    es_fin_de_semana            BOOLEAN,
    primary key (fecha_key)
);

create table gold.dim_hora (
    hora_key                    INTEGER,
    hora_etiqueta               VARCHAR,
    franja_horaria              VARCHAR,
    es_franja_pico              BOOLEAN,
    primary key (hora_key)
);

create table gold.dim_modo (
    modo_key                    INTEGER,
    modo_codigo                 VARCHAR,
    modo_nombre                 VARCHAR,
    unidad_registro             VARCHAR,
    formato_origen              VARCHAR,
    primary key (modo_key)
);

create table gold.dim_persona (
    persona_sk                  VARCHAR,
    tipo_identidad              VARCHAR,
    en_padron                   BOOLEAN,
    estado_padron               VARCHAR,
    perfil_vigente              VARCHAR,
    zona_residencia_key         VARCHAR,
    formato_llave_padron        VARCHAR,
    versiones_padron            BIGINT,
    primary key (persona_sk),
    foreign key (zona_residencia_key) references gold.dim_zona (zona_key)
);

create table gold.dim_zona (
    zona_key                    VARCHAR,
    zona_nombre                 VARCHAR,
    tipo_division               VARCHAR,
    municipio                   VARCHAR,
    puntos_de_abordaje          BIGINT,
    modos_con_servicio          BIGINT,
    modos_lista                 VARCHAR,
    tiene_servicio              BOOLEAN,
    primary key (zona_key)
);

create table gold.fct_abordaje (
    abordaje_id                 VARCHAR,
    persona_sk                  VARCHAR,
    modo_key                    INTEGER,
    estacion_key                VARCHAR,
    zona_key                    VARCHAR,
    fecha_key                   INTEGER,
    hora_key                    INTEGER,
    tipo_abordaje               VARCHAR,
    es_hora_pico                BOOLEAN,
    cantidad_abordajes          INTEGER,
    monto_q                     DECIMAL(10,2),
    primary key (abordaje_id),
    foreign key (estacion_key) references gold.dim_estacion (estacion_key),
    foreign key (fecha_key) references gold.dim_fecha (fecha_key),
    foreign key (hora_key) references gold.dim_hora (hora_key),
    foreign key (modo_key) references gold.dim_modo (modo_key),
    foreign key (persona_sk) references gold.dim_persona (persona_sk),
    foreign key (zona_key) references gold.dim_zona (zona_key)
);

create table gold.fct_estado_padron_diario (
    fecha_key                   INTEGER,
    persona_sk                  VARCHAR,
    zona_residencia_key         VARCHAR,
    perfil                      VARCHAR,
    estado                      VARCHAR,
    cantidad_personas           INTEGER,
    tarjetas_activas            INTEGER,
    primary key (fecha_key, persona_sk),
    foreign key (fecha_key) references gold.dim_fecha (fecha_key),
    foreign key (persona_sk) references gold.dim_persona (persona_sk),
    foreign key (zona_residencia_key) references gold.dim_zona (zona_key)
);

create table gold.fct_trayecto_od (
    trayecto_id                 VARCHAR,
    persona_sk                  VARCHAR,
    estacion_origen_key         VARCHAR,
    estacion_destino_key        VARCHAR,
    zona_origen_key             VARCHAR,
    zona_destino_key            VARCHAR,
    fecha_key                   INTEGER,
    hora_key                    INTEGER,
    es_hora_pico                BOOLEAN,
    cantidad_trayectos          INTEGER,
    duracion_s                  BIGINT,
    distancia_km                DOUBLE,
    monto_q                     DECIMAL(10,2),
    primary key (trayecto_id),
    foreign key (estacion_destino_key) references gold.dim_estacion (estacion_key),
    foreign key (estacion_origen_key) references gold.dim_estacion (estacion_key),
    foreign key (zona_destino_key) references gold.dim_zona (zona_key),
    foreign key (zona_origen_key) references gold.dim_zona (zona_key)
);
