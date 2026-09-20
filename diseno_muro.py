# =========================================================================================
# PROGRAMA: DISEÑO Y EVALUACIÓN DE MUROS DE CONTENCIÓN EN VOLADIZO (TODO EN UNO)
# =========================================================================================

import os
os.environ['MPLBACKEND'] = 'Agg'  # Gráficos eficientes sin ventanas emergentes
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from sections import _SinglePolygonSection


# =========================================================================================
#                             PANEL DE ENTRADA DE DATOS
#          (Modifica únicamente los valores dentro de esta sección para tu muro)
# =========================================================================================

# -----------------------------------------------------------------------------------------
# 1. GEOMETRÍA DEL MURO (Dimensiones en metros)
# -----------------------------------------------------------------------------------------
# Guía de Predimensionamiento usual:
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
key_depth   = 0.0     # [m] Profundidad del dentellón (0.0 si no tiene, ej: 0.35)
key_width   = 0.0     # [m] Ancho del dentellón (0.0 si no tiene, ej: 0.40)
key_pos     = 0.0     # [m] Posición desde la puntera (0.0 si no tiene, ej: 1.20)


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


# =========================================================================================
#                    MOTOR DE CÁLCULO POLIGONAL Y ESTRUCTURAL
# =========================================================================================

class CantileverWallSection(_SinglePolygonSection):
    """
    Modela la sección transversal completa de un muro de contención en voladizo
    de concreto reforzado como un polígono cerrado único.
    El origen (0, 0) se ubica en el pie de la puntera (toe inferior izquierdo).
    """
    def __init__(
        self,
        H: float,
        B: float,
        b_toe: float,
        h_f: float,
        b_stem_base: float,
        b_stem_top: float,
        gamma_c: float = 24.0,
        front_batter: float = 0.0,
        key_depth: float = 0.0,
        key_width: float = 0.0,
        key_pos: float = 0.0
    ):
        self.H = float(H)
        self.B = float(B)
        self.b_toe = float(b_toe)
        self.h_f = float(h_f)
        self.b_stem_base = float(b_stem_base)
        self.b_stem_top = float(b_stem_top)
        self.gamma_c = float(gamma_c)
        self.front_batter = float(front_batter)
        self.key_depth = float(key_depth)
        self.key_width = float(key_width)
        self.key_pos = float(key_pos)

        self.b_heel = self.B - self.b_toe - self.b_stem_base
        if self.b_heel < 0:
            raise ValueError(f"B ({self.B}) no puede ser menor que b_toe ({self.b_toe}) + b_stem_base ({self.b_stem_base})")
        if self.h_f >= self.H:
            raise ValueError(f"h_f ({self.h_f}) no puede ser mayor o igual a H ({self.H})")

        super().__init__()

    def _calculate_points(self):
        pts = [[0.0, 0.0]]

        # Dentellón (shear key) opcional
        if self.key_depth > 0 and self.key_width > 0:
            x_k1 = max(0.0, min(self.B, self.key_pos))
            x_k2 = max(0.0, min(self.B, self.key_pos + self.key_width))
            if x_k1 > 0:
                pts.append([x_k1, 0.0])
            pts.append([x_k1, -self.key_depth])
            pts.append([x_k2, -self.key_depth])
            if x_k2 < self.B:
                pts.append([x_k2, 0.0])

        pts.append([self.B, 0.0])
        pts.append([self.B, self.h_f])

        x_stem_base_rear = self.b_toe + self.b_stem_base
        pts.append([x_stem_base_rear, self.h_f])

        x_stem_top_rear = self.b_toe + self.front_batter + self.b_stem_top
        pts.append([x_stem_top_rear, self.H])

        x_stem_top_front = self.b_toe + self.front_batter
        pts.append([x_stem_top_front, self.H])

        pts.append([self.b_toe, self.h_f])
        pts.append([0.0, self.h_f])

        pts_array = np.array(pts, dtype=float)
        unique = [pts_array[0]]
        for pt in pts_array[1:]:
            if not np.allclose(pt, unique[-1], atol=1e-9):
                unique.append(pt)
        return np.array(unique, dtype=float)

    @property
    def centroid_x(self) -> float:
        """Centroide horizontal respecto al pie de la puntera (m)."""
        return float(self.y)

    @property
    def centroid_y(self) -> float:
        """Centroide vertical respecto a la base de la zapata (m)."""
        return float(self.z)

    @property
    def weight(self) -> float:
        """Peso propio del concreto por metro lineal de muro (kN/m)."""
        return float(self.area * self.gamma_c)

    @property
    def resisting_moment(self) -> float:
        """Momento estabilizador respecto al pie (0,0) (kN·m/m)."""
        return float(self.weight * self.centroid_x)


class HeelSoilSection(_SinglePolygonSection):
    """
    Modela la cuña de suelo de relleno sobre el talón del muro como polígono.
    """
    def __init__(self, wall: CantileverWallSection, gamma_s: float = 18.0, beta_deg: float = 0.0):
        self.wall = wall
        self.gamma_s = float(gamma_s)
        self.beta_rad = np.radians(float(beta_deg))
        super().__init__()

    def _calculate_points(self):
        x_stem_base_rear = self.wall.b_toe + self.wall.b_stem_base
        x_stem_top_rear = self.wall.b_toe + self.wall.front_batter + self.wall.b_stem_top
        y_base = self.wall.h_f
        y_top_stem = self.wall.H

        dx_slope = self.wall.B - x_stem_top_rear
        y_ground_at_B = y_top_stem + (dx_slope * np.tan(self.beta_rad) if dx_slope > 0 else 0.0)

        pts = [
            [x_stem_base_rear, y_base],
            [self.wall.B, y_base],
            [self.wall.B, y_ground_at_B],
            [x_stem_top_rear, y_top_stem]
        ]
        return np.array(pts, dtype=float)

    @property
    def centroid_x(self) -> float:
        return float(self.y)

    @property
    def centroid_y(self) -> float:
        """Centroide vertical del bloque de suelo (m)."""
        return float(self.z)

    @property
    def weight(self) -> float:
        return float(self.area * self.gamma_s)

    @property
    def resisting_moment(self) -> float:
        return float(self.weight * self.centroid_x)


class CantileverWallAnalysis:
    """
    Evaluación integral geotécnica (Rankine) y estructural (NSR-10 / ACI 318).
    """
    def __init__(
        self,
        wall: CantileverWallSection,
        gamma_s: float = 18.0,
        phi_s: float = 30.0,
        c_s: float = 0.0,
        q_surcharge: float = 0.0,
        beta_deg: float = 0.0,
        gamma_f: float = None,
        phi_f: float = None,
        c_f: float = 0.0,
        q_adm: float = 200.0,
        delta_ratio: float = 2.0 / 3.0,
        adhesion_ratio: float = 2.0 / 3.0,
        include_passive: bool = False
    ):
        self.wall = wall
        self.gamma_s = float(gamma_s)
        self.phi_s = float(phi_s)
        self.c_s = float(c_s)
        self.q_surcharge = float(q_surcharge)
        self.beta_deg = float(beta_deg)

        self.gamma_f = float(gamma_f if gamma_f is not None else gamma_s)
        self.phi_f = float(phi_f if phi_f is not None else phi_s)
        self.c_f = float(c_f)
        self.q_adm = float(q_adm)
        self.delta_ratio = float(delta_ratio)
        self.adhesion_ratio = float(adhesion_ratio)
        self.include_passive = bool(include_passive)

        self.soil_heel = HeelSoilSection(self.wall, gamma_s=self.gamma_s, beta_deg=self.beta_deg)
        self._calculate_active_pressure()
        self._calculate_external_stability()

    def _calculate_active_pressure(self):
        phi_rad = np.radians(self.phi_s)
        beta_rad = np.radians(self.beta_deg)

        if self.beta_deg == 0.0:
            self.Ka = np.tan(np.pi / 4.0 - phi_rad / 2.0) ** 2
        else:
            cos_b = np.cos(beta_rad)
            cos_phi = np.cos(phi_rad)
            num = cos_b - np.sqrt(cos_b ** 2 - cos_phi ** 2)
            den = cos_b + np.sqrt(cos_b ** 2 - cos_phi ** 2)
            self.Ka = cos_b * (num / den)

        x_stem_top_rear = self.wall.b_toe + self.wall.front_batter + self.wall.b_stem_top
        dx_slope = max(0.0, self.wall.B - x_stem_top_rear)
        h_slope = dx_slope * np.tan(beta_rad)
        self.H_eff = self.wall.H + h_slope + self.wall.key_depth

        self.Ea_soil_total = 0.5 * self.Ka * self.gamma_s * (self.H_eff ** 2)
        self.arm_soil = (self.H_eff / 3.0) - self.wall.key_depth

        self.Ea_q_total = self.Ka * self.q_surcharge * self.H_eff
        self.arm_q = (self.H_eff / 2.0) - self.wall.key_depth

        self.Ea_soil_h = self.Ea_soil_total * np.cos(beta_rad)
        self.Ea_soil_v = self.Ea_soil_total * np.sin(beta_rad)

        self.Ea_q_h = self.Ea_q_total * np.cos(beta_rad)
        self.Ea_q_v = self.Ea_q_total * np.sin(beta_rad)

        self.E_ah = self.Ea_soil_h + self.Ea_q_h
        self.E_av = self.Ea_soil_v + self.Ea_q_v
        self.M_v = self.Ea_soil_h * self.arm_soil + self.Ea_q_h * self.arm_q

    def _calculate_external_stability(self):
        self.W_c = self.wall.weight
        self.M_wc = self.wall.resisting_moment

        self.W_s = self.soil_heel.weight
        self.M_ws = self.soil_heel.resisting_moment

        x_stem_top_rear = self.wall.b_toe + self.wall.front_batter + self.wall.b_stem_top
        L_surcharge = max(0.0, self.wall.B - x_stem_top_rear)
        self.W_q = self.q_surcharge * L_surcharge
        x_q = (x_stem_top_rear + self.wall.B) / 2.0
        self.M_wq = self.W_q * x_q

        self.M_eav = self.E_av * self.wall.B
        self.sum_V = self.W_c + self.W_s + self.W_q + self.E_av
        self.M_R = self.M_wc + self.M_ws + self.M_wq + self.M_eav

        self.FS_v = self.M_R / self.M_v if self.M_v > 0 else float('inf')

        phi_f_rad = np.radians(self.phi_f)
        self.delta = self.delta_ratio * phi_f_rad
        self.c_a = self.adhesion_ratio * self.c_f

        self.E_p = 0.0
        if self.include_passive and self.wall.key_depth > 0:
            Kp = np.tan(np.pi / 4.0 + phi_f_rad / 2.0) ** 2
            d1 = self.wall.h_f
            d2 = self.wall.h_f + self.wall.key_depth
            self.E_p = 0.5 * Kp * self.gamma_f * (d2 ** 2 - d1 ** 2)

        self.F_R = self.sum_V * np.tan(self.delta) + self.c_a * self.wall.B
        self.R_sliding = self.F_R + self.E_p
        self.FS_d = self.R_sliding / self.E_ah if self.E_ah > 0 else float('inf')

        self.x_R = (self.M_R - self.M_v) / self.sum_V
        self.eccentricity = (self.wall.B / 2.0) - self.x_R
        self.e_limit = self.wall.B / 6.0
        self.in_middle_third = abs(self.eccentricity) <= self.e_limit

        if self.in_middle_third:
            self.q_toe = (self.sum_V / self.wall.B) * (1.0 + 6.0 * self.eccentricity / self.wall.B)
            self.q_heel = (self.sum_V / self.wall.B) * (1.0 - 6.0 * self.eccentricity / self.wall.B)
            self.q_max = max(self.q_toe, self.q_heel)
            self.q_min = min(self.q_toe, self.q_heel)
            self.contact_length = self.wall.B
        else:
            self.contact_length = max(0.01, 3.0 * self.x_R)
            self.q_max = (2.0 * self.sum_V) / (3.0 * self.x_R) if self.x_R > 0 else float('inf')
            self.q_min = 0.0
            self.q_toe = self.q_max
            self.q_heel = 0.0

        self.bearing_capacity_ok = (self.q_max <= self.q_adm)

    def design_stem(self, fc=21.0, fy=420.0, cover=0.05, phi_flexure=0.90, phi_shear=0.75):
        h_w = self.wall.H - self.wall.h_f
        b = 1.0
        bw = self.wall.b_stem_base

        phi_rad = np.radians(self.phi_s)
        Ka_stem = np.tan(np.pi / 4.0 - phi_rad / 2.0) ** 2
        Ea_stem_soil = 0.5 * Ka_stem * self.gamma_s * (h_w ** 2)
        Ea_stem_q = Ka_stem * self.q_surcharge * h_w

        Vu = 1.6 * Ea_stem_soil + 1.6 * Ea_stem_q
        Mu = 1.6 * (Ea_stem_soil * (h_w / 3.0) + Ea_stem_q * (h_w / 2.0))

        bar_est_diameter = 0.016
        d = bw - cover - (bar_est_diameter / 2.0)

        Mu_Nmm = Mu * 1e6
        b_mm = b * 1e3
        d_mm = d * 1e3

        Rn = Mu_Nmm / (phi_flexure * b_mm * (d_mm ** 2))
        disc = 1.0 - (2.0 * Rn) / (0.85 * fc)
        if disc < 0:
            raise ValueError(f"Sección insuficiente a flexión: Mu={Mu:.2f} kN·m.")

        rho_req = (0.85 * fc / fy) * (1.0 - np.sqrt(disc))
        rho_min_wall = 0.0015
        rho_design = max(rho_req, rho_min_wall)

        As_req_mm2 = rho_design * b_mm * d_mm
        As_req_cm2 = As_req_mm2 / 100.0

        Ast_mm2 = 0.0020 * b_mm * (bw * 1e3)
        Ast_cm2 = Ast_mm2 / 100.0

        rebar_db = {"#4 (1/2\")": 129.0, "#5 (5/8\")": 199.0, "#6 (3/4\")": 284.0, "#7 (7/8\")": 387.0, "#8 (1\")": 510.0}
        bar_options = []
        for name, area_bar in rebar_db.items():
            spacing_cm = int(((area_bar / As_req_mm2) * 1000.0) / 10.0)
            if 8 <= spacing_cm <= 40:
                bar_options.append((name, spacing_cm))

        Vc_N = 0.17 * np.sqrt(fc) * b_mm * d_mm
        phi_Vc_kN = (phi_shear * Vc_N) / 1000.0

        return {
            "Vu_kN": Vu, "Mu_kNm": Mu, "d_eff_cm": d * 100.0,
            "rho_design": rho_design, "As_req_cm2_m": As_req_cm2, "Ast_cm2_m": Ast_cm2,
            "bar_options": bar_options, "phi_Vc_kN": phi_Vc_kN, "shear_ok": (Vu <= phi_Vc_kN)
        }

    def summary(self) -> dict:
        return {
            "Geometria": {
                "H (m)": self.wall.H,
                "B (m)": self.wall.B,
                "Puntera b_toe (m)": self.wall.b_toe,
                "Talón b_heel (m)": self.wall.b_heel,
                "Espesor base zapata h_f (m)": self.wall.h_f,
                "Vástago base b_stem_base (m)": self.wall.b_stem_base,
                "Vástago corona b_stem_top (m)": self.wall.b_stem_top,
                "Dentellón (Prof x Ancho) (m)": f"{self.wall.key_depth:.2f} x {self.wall.key_width:.2f}"
            },
            "Pesos y Fuerzas Estabilizadoras": {
                "Peso Concreto Wc (kN/m)": self.W_c,
                "Centroide Concreto xc (m)": self.wall.centroid_x,
                "Momento Concreto M_wc (kN·m/m)": self.M_wc,
                "Peso Suelo Talón Ws (kN/m)": self.W_s,
                "Centroide Suelo xs (m)": self.soil_heel.centroid_x,
                "Momento Suelo M_ws (kN·m/m)": self.M_ws,
                "Sobrecarga Talón Wq (kN/m)": self.W_q,
                "Componente vertical empuje E_av (kN/m)": self.E_av,
                "Total Vertical sum_V (kN/m)": self.sum_V,
                "Momento Estabilizador Total M_R (kN·m/m)": self.M_R
            },
            "Empujes Activos y Momento Volcamiento": {
                "Coeficiente Ka": self.Ka,
                "Empuje Suelo Ea_soil_h (kN/m)": self.Ea_soil_h,
                "Brazo Suelo (m)": self.arm_soil,
                "Empuje Sobrecarga Ea_q_h (kN/m)": self.Ea_q_h,
                "Brazo Sobrecarga (m)": self.arm_q,
                "Empuje Horizontal Total E_ah (kN/m)": self.E_ah,
                "Momento Volcamiento M_v (kN·m/m)": self.M_v
            },
            "Estabilidad Geotécnica": {
                "FS Volcamiento (FS_v)": self.FS_v,
                "FS Volcamiento Cumple (>= 2.0)": self.FS_v >= 2.0,
                "Fuerza Resistente Deslizamiento F_R (kN/m)": self.R_sliding,
                "FS Deslizamiento (FS_d)": self.FS_d,
                "FS Deslizamiento Cumple (>= 1.5)": self.FS_d >= 1.5,
                "Punto Aplicación Resultante x_R (m)": self.x_R,
                "Excentricidad e (m)": self.eccentricity,
                "Límite Tercio Medio B/6 (m)": self.e_limit,
                "Tercio Medio Cumple (|e| <= B/6)": self.in_middle_third,
                "Presión Puntera q_toe (kPa)": self.q_toe,
                "Presión Talón q_heel (kPa)": self.q_heel,
                "Presión Máxima q_max (kPa)": self.q_max,
                "Capacidad Admisible q_adm (kPa)": self.q_adm,
                "Capacidad Portante Cumple": self.bearing_capacity_ok
            }
        }

    def print_report(self):
        s = self.summary()
        print("=" * 75)
        print("    EVALUACIÓN DE ESTABILIDAD GEOTÉCNICA Y ESTRUCTURAL DE MURO")
        print("                 Universidad Distrital Francisco José de Caldas")
        print("=" * 75)

        for sec_name, sec_dict in s.items():
            print(f"\n--- {sec_name.upper()} ---")
            for k, v in sec_dict.items():
                if isinstance(v, float):
                    print(f"  {k:<42}: {v:>10.3f}")
                elif isinstance(v, bool):
                    status = "APROBADO (OK)" if v else "NO CUMPLE (FALLA)"
                    print(f"  {k:<42}: {status:>18}")
                else:
                    print(f"  {k:<42}: {str(v):>18}")

        design = self.design_stem()
        print("\n--- DISEÑO ESTRUCTURAL DEL VÁSTAGO (NSR-10 / ACI 318) ---")
        print(f"  {'Cortante Último Vu (kN/m)':<42}: {design['Vu_kN']:>10.2f}")
        print(f"  {'Capacidad Cortante phi*Vc (kN/m)':<42}: {design['phi_Vc_kN']:>10.2f}")
        print(f"  {'Chequeo Cortante':<42}: {'CUMPLE (Vu <= phi*Vc)' if design['shear_ok'] else 'FALLA':>18}")
        print(f"  {'Momento Último Mu (kN·m/m)':<42}: {design['Mu_kNm']:>10.2f}")
        print(f"  {'Peralte Efectivo d (cm)':<42}: {design['d_eff_cm']:>10.2f}")
        print(f"  {'Cuantía de Diseño rho':<42}: {design['rho_design']:>10.4f}")
        print(f"  {'Acero Flexión As requerido (cm²/m)':<42}: {design['As_req_cm2_m']:>10.2f}")
        print(f"  {'Acero Temp. Ast requerido (cm²/m)':<42}: {design['Ast_cm2_m']:>10.2f}")
        print("  Opciones de Refuerzo Vertical:")
        for bar_name, sp in design["bar_options"]:
            print(f"     -> {bar_name} @ {sp} cm")
        print("=" * 75)

    def plot_complete_analysis(self, filename: str = None):
        plt.style.use('default')
        fig, ax = plt.subplots(figsize=(12, 9), dpi=150)

        # 1. Muro de concreto
        pts_wall = self.wall.points
        wall_polygon = patches.Polygon(pts_wall, closed=True, facecolor='#B0BEC5', edgecolor='#263238', linewidth=2, hatch='///', label='Muro de Concreto')
        ax.add_patch(wall_polygon)

        # 2. Suelo sobre el talón
        pts_soil = self.soil_heel.points
        soil_polygon = patches.Polygon(pts_soil, closed=True, facecolor='#FFE082', edgecolor='#F57F17', linewidth=1.5, alpha=0.6, hatch='...', label='Suelo sobre Talón')
        ax.add_patch(soil_polygon)

        # 3. Línea de terreno y sobrecarga
        x_stem_top_rear = self.wall.b_toe + self.wall.front_batter + self.wall.b_stem_top
        x_ground_end = self.wall.B + 1.2
        y_ground_start = self.wall.H
        y_ground_end = self.wall.H + (x_ground_end - x_stem_top_rear) * np.tan(np.radians(self.beta_deg))
        ax.plot([x_stem_top_rear, x_ground_end], [y_ground_start, y_ground_end], color='#8D6E63', linewidth=2.5, linestyle='-')

        if self.q_surcharge > 0:
            num_arrows = 6
            xs_q = np.linspace(x_stem_top_rear + 0.1, self.wall.B, num_arrows)
            arrow_len = 0.4
            for xq in xs_q:
                yq = self.wall.H + (xq - x_stem_top_rear) * np.tan(np.radians(self.beta_deg))
                ax.annotate('', xy=(xq, yq), xytext=(xq, yq + arrow_len),
                            arrowprops=dict(arrowstyle="->", color='#D84315', lw=1.5))
            ax.text((x_stem_top_rear + self.wall.B) / 2.0, self.wall.H + arrow_len + 0.15,
                    f"Sobrecarga q = {self.q_surcharge:.1f} kPa", ha='center', color='#D84315', fontsize=10, fontweight='bold')

        # 4. Diagrama de empuje activo lateral
        y_bottom_plane = -self.wall.key_depth
        y_top_plane = y_ground_start + (self.wall.B - x_stem_top_rear) * np.tan(np.radians(self.beta_deg))
        ax.plot([self.wall.B, self.wall.B], [y_bottom_plane, y_top_plane], color='#D32F2F', linestyle='--', linewidth=1.5)

        pa_base = self.Ka * self.gamma_s * self.H_eff + self.Ka * self.q_surcharge
        scale_pressure = 1.0 / max(pa_base, 1.0) * 1.0
        x_pa_base = self.wall.B + pa_base * scale_pressure
        x_pa_top = self.wall.B + (self.Ka * self.q_surcharge) * scale_pressure

        pts_lateral = [
            [self.wall.B, y_bottom_plane],
            [x_pa_base, y_bottom_plane],
            [x_pa_top, y_top_plane],
            [self.wall.B, y_top_plane]
        ]
        lateral_patch = patches.Polygon(pts_lateral, closed=True, facecolor='#FFCDD2', edgecolor='#D32F2F', alpha=0.5, hatch='\\\\', label='Empuje Activo Ea')
        ax.add_patch(lateral_patch)

        y_act = (self.Ea_soil_h * self.arm_soil + self.Ea_q_h * self.arm_q) / self.E_ah
        ax.annotate(f"Eah = {self.E_ah:.1f} kN/m", xy=(self.wall.B, y_act), xytext=(self.wall.B + 1.2, y_act),
                    arrowprops=dict(facecolor='#D32F2F', edgecolor='#B71C1C', width=2, headwidth=8),
                    color='#B71C1C', fontweight='bold', fontsize=10, va='center')

        # 5. Presiones en la base
        q_scale = 0.7 / max(self.q_max, 1.0)
        y_q_toe = -self.wall.key_depth - 0.2
        y_q_heel = -self.wall.key_depth - 0.2

        if self.in_middle_third:
            pts_q = [
                [0.0, y_q_toe],
                [0.0, y_q_toe - self.q_toe * q_scale],
                [self.wall.B, y_q_heel - self.q_heel * q_scale],
                [self.wall.B, y_q_heel]
            ]
        else:
            pts_q = [
                [0.0, y_q_toe],
                [0.0, y_q_toe - self.q_max * q_scale],
                [self.contact_length, y_q_heel],
                [0.0, y_q_heel]
            ]
        q_patch = patches.Polygon(pts_q, closed=True, facecolor='#C8E6C9', edgecolor='#2E7D32', alpha=0.7, label='Presión Terreno')
        ax.add_patch(q_patch)

        ax.text(0.0, y_q_toe - self.q_toe * q_scale - 0.15, f"q_max = {self.q_max:.1f} kPa", ha='center', color='#1B5E20', fontweight='bold', fontsize=9)
        if self.in_middle_third:
            ax.text(self.wall.B, y_q_heel - self.q_heel * q_scale - 0.15, f"q_min = {self.q_min:.1f} kPa", ha='center', color='#1B5E20', fontweight='bold', fontsize=9)
        else:
            ax.text(self.contact_length, y_q_heel - 0.15, f"q = 0 (L_c={self.contact_length:.2f} m)", ha='left', color='#C62828', fontsize=8)

        # 6. Resultante vertical
        ax.annotate(f"ΣV = {self.sum_V:.1f} kN/m\n(xR = {self.x_R:.2f} m)", xy=(self.x_R, 0.0), xytext=(self.x_R, -1.0),
                    arrowprops=dict(facecolor='#1565C0', edgecolor='#0D47A1', width=2, headwidth=8),
                    color='#0D47A1', fontweight='bold', fontsize=9, ha='center')

        # 7. Centroides
        ax.plot(self.wall.centroid_x, self.wall.centroid_y, 'ro', markersize=7, label=f'C.G. Muro ({self.wall.centroid_x:.2f}, {self.wall.centroid_y:.2f})')
        ax.plot(self.soil_heel.centroid_x, self.soil_heel.centroid_y, 's', color='#E65100', markersize=7, label=f'C.G. Suelo ({self.soil_heel.centroid_x:.2f}, {self.soil_heel.centroid_y:.2f})')

        # 8. Cuadro de Resumen
        status_v = "OK" if self.FS_v >= 2.0 else "FALLA"
        status_d = "OK" if self.FS_d >= 1.5 else "FALLA"
        status_e = "OK" if self.in_middle_third else "FALLA"
        status_q = "OK" if self.bearing_capacity_ok else "FALLA"

        design_stem = self.design_stem()
        status_shear = "OK" if design_stem['shear_ok'] else "FALLA"

        text_box = (
            r"$\mathbf{EVALUACIÓN\ DE\ ESTABILIDAD}$" + "\n"
            f"• FS Volcamiento: {self.FS_v:.2f} (≥ 2.0) -> {status_v}\n"
            f"• FS Deslizamiento: {self.FS_d:.2f} (≥ 1.5) -> {status_d}\n"
            f"• Excentricidad e: {self.eccentricity:.3f} m (B/6 = {self.e_limit:.3f} m) -> {status_e}\n"
            f"• Presión q_max: {self.q_max:.1f} kPa (q_adm = {self.q_adm:.1f} kPa) -> {status_q}\n"
            r"$\mathbf{DISEÑO\ ESTRUCTURAL\ (NSR-10)}$" + "\n"
            f"• Mu: {design_stem['Mu_kNm']:.1f} kN·m/m | Vu: {design_stem['Vu_kN']:.1f} kN/m\n"
            f"• Cortante ϕVc: {design_stem['phi_Vc_kN']:.1f} kN/m -> {status_shear}\n"
            f"• As req: {design_stem['As_req_cm2_m']:.2f} cm²/m\n"
        )
        if design_stem["bar_options"]:
            text_box += f"• Refuerzo: {design_stem['bar_options'][0][0]} @ {design_stem['bar_options'][0][1]} cm"

        props = dict(boxstyle='round,pad=0.6', facecolor='#F5F5F5', alpha=0.95, edgecolor='#37474F', linewidth=1.5)
        ax.text(0.03, 0.96, text_box, transform=ax.transAxes, fontsize=10, verticalalignment='top', bbox=props)

        ax.set_aspect('equal', adjustable='box')
        ax.set_xlabel('Ancho X (m)', fontsize=11, fontweight='bold')
        ax.set_ylabel('Elevación Y (m)', fontsize=11, fontweight='bold')
        ax.set_title('Evaluación Geotécnica y Estructural de Muro de Contención en Voladizo\n(Geometría calculada con pysections)',
                     fontsize=12, fontweight='bold', pad=15)
        ax.grid(True, linestyle=':', alpha=0.6)
        ax.legend(loc='lower right', framealpha=0.9)

        y_min_lim = min(-self.wall.key_depth - 1.5, y_q_toe - self.q_max * q_scale - 0.5)
        y_max_lim = max(self.wall.H + 1.0, y_ground_end + 0.8)
        ax.set_ylim(y_min_lim, y_max_lim)
        ax.set_xlim(-0.8, max(self.wall.B + 2.0, x_ground_end + 0.5))

        plt.tight_layout()
        if filename:
            plt.savefig(filename, bbox_inches='tight', dpi=200)
            print(f"Gráfico guardado exitosamente en: {filename}")
        else:
            plt.show()


# =========================================================================================
#                               EJECUCIÓN PRINCIPAL
# =========================================================================================

def main():
    print("\nIniciando cálculo del muro de contención...")

    # 1. Creación del modelo geométrico del muro
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
