# =========================================================================================
# UNIVERSIDAD DISTRITAL FRANCISCO JOSÉ DE CALDAS
# FACULTAD DE INGENIERÍA - INGENIERÍA CIVIL
# PROGRAMACIÓN II / GEOTECNIA / ESTRUCTURAS
#
# PROGRAMA: DISEÑO Y EVALUACIÓN DE MUROS DE CONTENCIÓN EN VOLADIZO
# Motor poligonal: pysections (sections.py)
# Normas: NSR-10 Título C / ACI 318 / Teoría de Rankine
# =========================================================================================

import os
os.environ['MPLBACKEND'] = 'Agg'  # Gráficos eficientes
from retaining_wall import CantileverWallSection, CantileverWallAnalysis


# =========================================================================================
#                             PANEL DE ENTRADA DE DATOS
#          (Modifica únicamente los valores dentro de esta sección para tu muro)
# =========================================================================================

# -----------------------------------------------------------------------------------------
# 1. GEOMETRÍA DEL MURO (Dimensiones en metros)
# -----------------------------------------------------------------------------------------
# Criterios de Predimensionamiento usual:
#   - B (ancho zapata)      : entre 0.50*H y 0.70*H
#   - b_toe (puntera)       : entre B/3 y B/4 (aprox. 0.10*H a 0.15*H)
#   - h_f (espesor zapata)  : entre H/12 y H/10 (mínimo 0.30 m)
#   - b_stem_base (vástago) : entre H/12 y H/10 (en la base)
#   - b_stem_top (corona)   : mínimo 0.25 m a 0.30 m (para vaciado de concreto)
# -----------------------------------------------------------------------------------------
H           = 5.00    # [m] Altura total del muro (desde fondo de zapata hasta la corona)
B           = 3.20    # [m] Ancho total de la zapata (base)
b_toe       = 0.80    # [m] Longitud de la puntera (pie delantero)
h_f         = 0.50    # [m] Espesor de la zapata (losa de cimentación)
b_stem_base = 0.50    # [m] Espesor del vástago en su unión con la zapata
b_stem_top  = 0.30    # [m] Espesor del vástago en la corona superior
gamma_c     = 24.0    # [kN/m³] Peso específico del concreto reforzado

# Inclinación de la cara frontal (opcional, 0.0 = cara vertical recta):
front_batter = 0.0    # [m] Desfase horizontal de la cara frontal

# Dentellón / Shear Key (Opcional - Actívalo si falla al deslizamiento):
key_depth = 0.0       # [m] Profundidad del dentellón hacia abajo (0.0 si no tiene)
key_width = 0.0       # [m] Ancho del dentellón (0.0 si no tiene)
key_pos   = 0.0       # [m] Distancia desde la punta de la puntera hasta el dentellón


# -----------------------------------------------------------------------------------------
# 2. SUELO DE RELLENO RETENIDO Y CARGAS SUPERFICIALES
# -----------------------------------------------------------------------------------------
gamma_s     = 18.5    # [kN/m³] Peso unitario del relleno (típico: 17.0 - 20.0 kN/m³)
phi_s       = 32.0    # [grados] Ángulo de fricción interna del relleno (típico: 28° - 35°)
c_s         = 0.0     # [kPa] Cohesión del relleno (0.0 para material granular filtrante)
q_surcharge = 15.0    # [kPa] Sobrecarga uniforme sobre el terreno (tráfico: 10 - 20 kPa)
beta_deg    = 0.0     # [grados] Inclinación del talud del terreno (0.0 = terreno plano)


# -----------------------------------------------------------------------------------------
# 3. SUELO DE FUNDACIÓN (Terreno de apoyo bajo la zapata)
# -----------------------------------------------------------------------------------------
q_adm       = 220.0   # [kPa] Capacidad portante admisible del suelo (del estudio de suelos)
phi_f       = 30.0    # [grados] Fricción del suelo de fundación (para fricción base-suelo)
c_f         = 10.0    # [kPa] Cohesión del suelo de fundación (0.0 si es arena pura)
gamma_f     = 19.0    # [kN/m³] Peso unitario del suelo bajo la zapata


# -----------------------------------------------------------------------------------------
# 4. MATERIALES PARA DISEÑO ESTRUCTURAL (NSR-10 Título C / ACI 318)
# -----------------------------------------------------------------------------------------
fc          = 21.0    # [MPa] Resistencia a compresión del concreto f'c (21 MPa ≈ 210 kg/cm²)
fy          = 420.0   # [MPa] Límite de fluencia del acero de refuerzo fy (Grado 60)
cover       = 0.05    # [m] Recubrimiento libre de concreto hacia el terreno (5 cm)


# -----------------------------------------------------------------------------------------
# 5. CONFIGURACIÓN DE SALIDA
# -----------------------------------------------------------------------------------------
archivo_imagen = "resultado_muro.png"   # Nombre de la imagen donde se guardará el plano
# =========================================================================================
#                       FIN DEL PANEL DE ENTRADA DE DATOS
#                (No necesitas modificar nada a partir de aquí)
# =========================================================================================


def main():
    print("\nIniciando cálculo del muro de contención...")

    # 1. Creación del modelo geométrico del muro con el motor poligonal de sections.py
    muro = CantileverWallSection(
        H=H,
        B=B,
        b_toe=b_toe,
        h_f=h_f,
        b_stem_base=b_stem_base,
        b_stem_top=b_stem_top,
        gamma_c=gamma_c,
        front_batter=front_batter,
        key_depth=key_depth,
        key_width=key_width,
        key_pos=key_pos
    )

    # 2. Análisis geotécnico y estructural completo
    analisis = CantileverWallAnalysis(
        wall=muro,
        gamma_s=gamma_s,
        phi_s=phi_s,
        c_s=c_s,
        q_surcharge=q_surcharge,
        beta_deg=beta_deg,
        gamma_f=gamma_f,
        phi_f=phi_f,
        c_f=c_f,
        q_adm=q_adm,
        delta_ratio=2.0 / 3.0,
        adhesion_ratio=2.0 / 3.0,
        include_passive=False
    )

    # 3. Impresión del reporte técnico en pantalla
    analisis.print_report()

    # 4. Generación y guardado del gráfico con el diagrama de estabilidad
    ruta_guardado = os.path.join(os.path.dirname(os.path.abspath(__file__)), archivo_imagen)
    analisis.plot_complete_analysis(filename=ruta_guardado)
    print(f"\n[OK] El gráfico del muro ha sido generado exitosamente en:\n     -> {ruta_guardado}\n")


if __name__ == "__main__":
    main()
