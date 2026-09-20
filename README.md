
# Cantilever Retaining Wall Design & Stability Analysis Repository
**Repositorito de Diseño-y-Evaluación-Integral-de-Muros-de-Contención-en-Voladizo**

---

## 1. Introduction (Introducción)

Este repositorio contiene una herramienta computacional en Python para el diseño y análisis integral de **Muros de Contención en Voladizo** de concreto reforzado. El proyecto resuelve de forma automatizada y simultánea dos aspectos fundamentales de la ingeniería civil:

1. **Estabilidad Geotécnica Externa:** Verificación de factores de seguridad contra volcamiento ($FS_v$), deslizamiento ($FS_d$), excentricidad dentro del tercio medio ($e \le B/6$) y presiones de contacto sobre el suelo de fundación ($q_{max} \le q_{adm}$).
2. **Diseño Estructural Interno (NSR-10 / ACI 318):** Cálculo de solicitaciones últimas a flexión y cortante en la base del vástago, determinación de la cuantía de acero longitudinal ($A_s$), selección de barras comerciales y espaciamientos, acero de retracción y temperatura ($A_{st}$) y verificación de la capacidad a cortante del concreto ($\phi V_c$).

---

## 2. Background & Antecedentes (¿Qué se usó de `pysections`?)

El diseño tradicional de muros de contención suele recurrir a simplificaciones geométricas o a software comercial cerrado para determinar las áreas y centroides del concreto y de las cuñas de suelo retenido. 

Este proyecto se fundamenta directamente en el motor de cálculo poligonal del repositorio [**pysections**](https://github.com/rvcristiand/pysections) (desarrollado por Cristian Danilo Ramírez Vargas), el cual calcula propiedades de secciones transversales arbitrarias a través del **Teorema de Green / Fórmula del Agrimensor (Gauss)**.

### Componentes específicos utilizados de `sections.py`:
* **Clase `Section`:** Actúa como motor de cálculo interno numérico. Se utilizan sus métodos vectorizados:
  * `_A(points)`: Cálculo del área exacta de cualquier polígono cerrado.
  * `_Qx(points)` y `_Qy(points)`: Momentos estáticos de primer orden de área.
  * `_x(points)` y `_y(points)`: Localización exacta del centroide baricéntrico $(\bar{x}, \bar{y})$.
  * `_Ixx(points)` y `_Iyy(points)`: Momentos de inercia baricéntricos mediante el Teorema de Steiner.
* **Clase abstracta `_SinglePolygonSection (ABC)`:**
  * Se hereda de esta clase para construir las secciones del muro y del suelo mediante polígonos cerrados de un solo contorno.
  * Al implementar el método abstracto `_calculate_points()`, se accede limpiamente a las propiedades `@property` (`area`, `centroid_x`, `centroid_y`, `weight`, `resisting_moment`).

### Innovación del modelado con `_SinglePolygonSection`:
1. **Concreto del Muro (`CantileverWallSection`):** Se modela como un polígono cerrado único con zapata, puntera, talón, vástago de sección variable y dentellón (*shear key*) opcional. Esto permite obtener de manera exacta el peso propio del concreto ($W_c = \gamma_c \cdot A_c$) y su brazo estabilizador ($\bar{x}_c$) respecto al pie de la puntera $(0,0)$.
2. **Bloque de Suelo sobre el Talón (`HeelSoilSection`):** Se modela la masa de suelo de relleno gravitante sobre el talón como otro polígono, calculando automáticamente su área ($A_s$), peso ($W_s = \gamma_s \cdot A_s$) y centroide horizontal ($\bar{x}_s$) incluso con talud inclinado ($\beta$).

---

## 3. Code Structure (Estructura del Código)

Para facilitar su uso e instalación, el proyecto está contenido en **un único archivo de diseño** que se apoya en el motor base:

```text
pysections-main/
│
├── sections.py              # Motor poligonal base (repositorio upstream: rvcristiand/pysections)
│   ├── Section              <- Motor de cálculo (Green / Gauss / Steiner)
│   └── _SinglePolygonSection<- Clase abstracta para polígonos cerrados
│
├── diseno_muro.py           # SCRIPT PRINCIPAL (TODO EN UNO):
│   ├── Panel de Entrada     <- Zona superior donde el usuario coloca sus datos
│   ├── CantileverWallSection<- Modela el muro completo heredando de _SinglePolygonSection
│   ├── HeelSoilSection      <- Modela la cuña de suelo heredando de _SinglePolygonSection
│   └── CantileverWallAnalysis<- Motor de empujes (Rankine), estabilidad externa y NSR-10
│
├── requirements.txt         # Dependencias del proyecto (numpy, matplotlib)
└── README.md                # Documentación del proyecto
```

---

## 4. How It Works: Theoretical Framework (Cómo Funciona: Marco Matemático)

Tomando como origen de coordenadas $(0,0)$ el extremo inferior izquierdo de la puntera (*toe*):

```text
       b_stem_top (corona)
           +--+
           |  |
           |  |  Relleno (γs, φs, cs, q, β)
           |  |
   bw      +--+
+------+      +---------+
|                       | h_f (zapata)
+-----------------------+
(0,0)         B (base)
```

### 4.1 Empuje Activo de Tierras (Teoría de Rankine)
Para un relleno granular con sobrecarga superficial $q$ e inclinación $\beta$:
$$K_a = \cos\beta \frac{\cos\beta - \sqrt{\cos^2\beta - \cos^2\phi}}{\cos\beta + \sqrt{\cos^2\beta - \cos^2\phi}}$$
$$E_{a,suelo} = \frac{1}{2} K_a \gamma_s H_{eff}^2, \quad y_{suelo} = \frac{H_{eff}}{3}$$
$$E_{a,q} = K_a q H_{eff}, \quad y_{q} = \frac{H_{eff}}{2}$$
$$M_v = E_{ah,suelo} \cdot y_{suelo} + E_{ah,q} \cdot y_{q}$$

### 4.2 Fuerzas y Momentos Estabilizadores
Aprovechando `_SinglePolygonSection`:
$$\sum V = W_c + W_s + W_q + E_{av} = \gamma_c A_c + \gamma_s A_s + q \cdot b_{talon} + E_{av}$$
$$M_R = W_c \cdot \bar{x}_c + W_s \cdot \bar{x}_s + W_q \cdot \bar{x}_q + E_{av} \cdot B$$

### 4.3 Factores de Seguridad y Presiones de Contacto
* **Volcamiento:**
  $$FS_v = \frac{M_R}{M_v} \ge 2.0$$
* **Deslizamiento:**
  $$FS_d = \frac{\sum V \cdot \tan(2/3 \phi_f) + c_a B + E_p}{E_{ah}} \ge 1.5$$
* **Excentricidad (Tercio Medio):**
  $$x_R = \frac{M_R - M_v}{\sum V}, \quad e = \frac{B}{2} - x_R \le \frac{B}{6}$$
* **Presiones de Contacto:**
  $$q_{max, min} = \frac{\sum V}{B} \left(1 \pm \frac{6e}{B}\right) \le q_{adm}$$

### 4.4 Diseño Estructural del Vástago (NSR-10 / ACI 318)
* **Combinación de Carga Mayorada:** $U = 1.6 H + 1.6 L$
* **Cortante en Concreto:** $V_u \le \phi V_c = 0.75 \cdot \left(0.17 \sqrt{f'_c} b d\right)$
* **Acero a Flexión:** Cuantía requerida $\rho = \frac{0.85 f'_c}{f_y} \left(1 - \sqrt{1 - \frac{2 M_u}{\phi \cdot 0.85 f'_c b d^2}}\right)$, con $A_s = \max(\rho, \rho_{min}) b d$.

---

## 5. Installation Guide: Step-by-Step for Ubuntu (Instalación Paso a Paso)

Sigue estos comandos en una terminal limpia de **Ubuntu**:

### Paso 1: Actualizar el sistema e instalar Python y herramientas
```bash
sudo apt update && sudo apt upgrade -y
sudo apt install python3 python3-pip python3-venv git -y
```

### Paso 2: Clonar el repositorio base `pysections`
Descarga la librería base de secciones poligonales desde GitHub:
```bash
git clone https://github.com/rvcristiand/pysections.git
cd pysections
```

### Paso 3: Crear y activar un entorno virtual
```bash
python3 -m venv venv
source venv/bin/activate
```
*(Aparecerá `(venv)` al inicio de tu terminal indicando que el entorno está activo).*

### Paso 4: Instalar las dependencias de Python
```bash
pip install numpy matplotlib
```

### Paso 5: Añadir el archivo de diseño
Asegúrate de tener el archivo **`diseno_muro.py`** en la misma carpeta donde reside `sections.py`.

---

## 6. Usage: Basic Example (`diseno_muro.py`)

Para analizar un muro, abre `diseno_muro.py` con cualquier editor (ej: `nano diseno_muro.py`), edita los parámetros en el **PANEL DE ENTRADA DE DATOS** ubicado al inicio del archivo:

```python
# =========================================================================
#                       PANEL DE ENTRADA DE DATOS
# =========================================================================
# 1. Geometría del Muro (metros)
H           = 5.00    # [m] Altura total del muro (desde fondo zapata hasta corona)
B           = 3.20    # [m] Ancho total de la zapata (base)
b_toe       = 0.80    # [m] Longitud de la puntera (pie delantero)
h_f         = 0.50    # [m] Espesor de la zapata
b_stem_base = 0.50    # [m] Espesor del vástago en la base
b_stem_top  = 0.30    # [m] Espesor de la corona superior
gamma_c     = 24.0    # [kN/m³] Peso específico del concreto
# Inclinación frontal y dentellón (opcionales)
front_batter = 0.0    # [m] Desfase cara frontal (0.0 = vertical)
key_depth    = 0.0    # [m] Profundidad dentellón (ej: 0.35 si falla deslizamiento)
key_width    = 0.0    # [m] Ancho del dentellón (ej: 0.40)
key_pos      = 0.0    # [m] Distancia desde la puntera (ej: 1.20)
# 2. Suelo de Relleno y Sobrecarga
gamma_s     = 18.5    # [kN/m³] Peso unitario del relleno
phi_s       = 32.0    # [grados] Ángulo de fricción interna del relleno
c_s         = 0.0     # [kPa] Cohesión del relleno (0.0 para granular)
q_surcharge = 15.0    # [kPa] Sobrecarga uniforme de tránsito
beta_deg    = 0.0     # [grados] Inclinación del talud del terreno
# 3. Suelo de Fundación (Apoyo bajo la zapata)
q_adm       = 220.0   # [kPa] Capacidad portante admisible del terreno
phi_f       = 30.0    # [grados] Fricción del suelo de fundación
c_f         = 10.0    # [kPa] Cohesión del suelo bajo la zapata
gamma_f     = 19.0    # [kN/m³] Peso unitario bajo la zapata
# 4. Materiales Estructurales (NSR-10 / ACI 318)
fc          = 21.0    # [MPa] Resistencia f'c del concreto (21 MPa ≈ 210 kg/cm²)
fy          = 420.0   # [MPa] Límite de fluencia del acero (Grado 60)
cover       = 0.05    # [m] Recubrimiento libre de concreto (5 cm)
# 5. Configuración de salida
archivo_imagen = "resultado_muro.png"
```
### Ejecución en Terminal:
Una vez guardados los datos, ejecuta el archivo directamente:
```bash
python3 diseno_muro.py
```
### Salida en Consola:
```text
===========================================================================
    EVALUACIÓN DE ESTABILIDAD GEOTÉCNICA Y ESTRUCTURAL DE MURO
                 Universidad Distrital Francisco José de Caldas
===========================================================================
--- GEOMETRIA ---
  H (m)                                     :      5.000
  B (m)                                     :      3.200
  Puntera b_toe (m)                         :      0.800
  Talón b_heel (m)                          :      1.900
  Espesor base zapata h_f (m)               :      0.500
  Vástago base b_stem_base (m)              :      0.500
  Vástago corona b_stem_top (m)             :      0.300
  Dentellón (Prof x Ancho) (m)              :        0.00 x 0.00
--- ESTABILIDAD GEOTÉCNICA ---
  FS Volcamiento (FS_v)                     :      3.060 -> APROBADO (OK)
  FS Deslizamiento (FS_d)                   :      1.308 -> NO CUMPLE (FALLA)
  Punto Aplicación Resultante x_R (m)       :      1.297
  Excentricidad e (m)                       :      0.303 (B/6 = 0.533 m) -> APROBADO (OK)
  Presión Máxima q_max (kPa)                :    136.996 (q_adm = 220 kPa) -> APROBADO (OK)
--- DISEÑO ESTRUCTURAL DEL VÁSTAGO (NSR-10 / ACI 318) ---
  Cortante Último Vu (kN/m)                 :     125.27
  Capacidad Cortante phi*Vc (kN/m)          :     258.25 -> CUMPLE (Vu <= phi*Vc)
  Momento Último Mu (kN·m/m)                :     212.79
  Peralte Efectivo d (cm)                   :      44.20
  Acero Flexión As requerido (cm²/m)        :      13.20
  Acero Temp. Ast requerido (cm²/m)         :      10.00
  Opciones de Refuerzo Vertical:
     -> #5 (5/8") @ 15 cm
     -> #6 (3/4") @ 21 cm
     -> #7 (7/8") @ 29 cm
===========================================================================
```
### Para visualizar el plano gráfico en Ubuntu:
```bash
xdg-open resultado_muro.png
```

---

## 7. Dependencies (Dependencias)

Este proyecto requiere Python 3.10+ y las siguientes librerías:
* `numpy >= 1.24.0`
* `matplotlib >= 3.7.0`

---

## 8. Contributions & Credits (Créditos y Contribuciones)

* **Motor Poligonal Base:** [Cristian Danilo Ramírez Vargas (pysections)](https://github.com/rvcristiand/pysections).
* Las contribuciones son bienvenidas. Si encuentras errores o deseas proponer mejoras, siéntete libre de abrir un *issue* o enviar un *pull request*.
