from qgis.core import *
from PyQt5.QtGui import QColor
import processing
import os

# === CAMINHOS ===
folder = r'C:/Users/estag/OneDrive/Área de Trabalho/OneDrive/Documentos/OneDrive/AMPLAR GS/HeatMap/LC09_L2SP_219076_20241126_20241127_02_T1'
shapefile_amparo = r"C:\Users\estag\OneDrive\Área de Trabalho\OneDrive\Documentos\OneDrive\AMPLAR GS\HeatMap\AmparoShape\Amparo-city.shp"

b4 = os.path.join(folder, 'LC09_L2SP_219076_20241126_20241127_02_T1_SR_B4.TIF')  # Red
b5 = os.path.join(folder, 'LC09_L2SP_219076_20241126_20241127_02_T1_SR_B5.TIF')  # NIR
b10 = os.path.join(folder, 'LC09_L2SP_219076_20241126_20241127_02_T1_ST_B10.TIF')  # Thermal

ndvi_path = os.path.join(folder, 'ndvi.tif')
emissivity_path = os.path.join(folder, 'emissivity.tif')
temp_kelvin_path = os.path.join(folder, 'temp_kelvin.tif')
temp_celsius_path = os.path.join(folder, 'temp_celsius.tif')
ilhas_path = os.path.join(folder, 'ilhas_classificadas.tif')

# === NDVI ===
processing.run("gdal:rastercalculator", {
    'INPUT_A': b5, 'BAND_A': 1,
    'INPUT_B': b4, 'BAND_B': 1,
    'FORMULA': '(A - B) / (A + B + 0.00001)',
    'OUTPUT': ndvi_path,
    'RTYPE': 5
})

# === EMISSIVIDADE BASEADA EM NDVI ===
# Fórmula: ε = 0.004 * PV + 0.986, onde PV = ((NDVI - NDVImin)/(NDVImax - NDVImin))²
ndvi_layer = QgsRasterLayer(ndvi_path, "NDVI")
provider = ndvi_layer.dataProvider()
stats = provider.bandStatistics(1)
ndvi_min = stats.minimumValue
ndvi_max = stats.maximumValue

pv_formula = f"((A - {ndvi_min}) / ({ndvi_max - ndvi_min})) ** 2"
emissivity_formula = f"(0.004 * ((A - {ndvi_min}) / ({ndvi_max - ndvi_min})) ** 2) + 0.986"

processing.run("gdal:rastercalculator", {
    'INPUT_A': ndvi_path, 'BAND_A': 1,
    'FORMULA': emissivity_formula,
    'OUTPUT': emissivity_path,
    'RTYPE': 5
})

# === TEMPERATURA EM KELVIN USANDO EMISSIVIDADE ===
k1 = 774.8853
k2 = 1321.0789
mult = 0.0003342
add = 0.1
radiance_formula = f"(A * {mult}) + {add}"

# 1. Radiância (intermediária)
radiance_path = os.path.join(folder, 'radiance.tif')
processing.run("gdal:rastercalculator", {
    'INPUT_A': b10, 'BAND_A': 1,
    'FORMULA': radiance_formula,
    'OUTPUT': radiance_path,
    'RTYPE': 5
})

# 2. Temperatura de Superfície com emissividade
ts_formula = f"({k2} / log(({k1} / (A / B)) + 1))"
processing.run("gdal:rastercalculator", {
    'INPUT_A': radiance_path, 'BAND_A': 1,
    'INPUT_B': emissivity_path, 'BAND_B': 1,
    'FORMULA': ts_formula,
    'OUTPUT': temp_kelvin_path,
    'RTYPE': 5
})

# 3. Conversão para °C
processing.run("gdal:rastercalculator", {
    'INPUT_A': temp_kelvin_path, 'BAND_A': 1,
    'FORMULA': "A - 273.15",
    'OUTPUT': temp_celsius_path,
    'RTYPE': 5
})

# === CLASSIFICAÇÃO DAS ILHAS DE CALOR ===
# 1 = Moderada (NDVI<0.3 & temp 30–33), 2 = Alta (NDVI<0.2 & temp 33–36), 3 = Crítica (NDVI<0.15 & temp>36)
processing.run("gdal:rastercalculator", {
    'INPUT_A': ndvi_path, 'BAND_A': 1,
    'INPUT_B': temp_celsius_path, 'BAND_B': 1,
    'FORMULA': '((A<0.3)*(B>30)*(B<=33))*1 + ((A<0.2)*(B>33)*(B<=36))*2 + ((A<0.15)*(B>36))*3',
    'OUTPUT': ilhas_path,
    'RTYPE': 1
})

# === RECORTE PARA AMPARO ===
camadas = [
    (ndvi_path, os.path.join(folder, 'ndvi_amparo.tif')),
    (temp_celsius_path, os.path.join(folder, 'temp_amparo.tif')),
    (ilhas_path, os.path.join(folder, 'ilhas_amparo.tif'))
]

for entrada, saida in camadas:
    processing.run("gdal:cliprasterbymasklayer", {
        'INPUT': entrada,
        'MASK': shapefile_amparo,
        'CROP_TO_CUTLINE': True,
        'OUTPUT': saida
    })

# === SIMBOLOGIA FINAL ===
def aplicar_simbologia(layer, tipo):
    shader = QgsColorRampShader()
    shader.setColorRampType(QgsColorRampShader.Interpolated)

    if tipo == "ilhas":
        shader.setColorRampItemList([
            QgsColorRampShader.ColorRampItem(0, QColor(0, 0, 0, 0), "Sem risco"),
            QgsColorRampShader.ColorRampItem(1, QColor("#FFD700"), "Moderada"),
            QgsColorRampShader.ColorRampItem(2, QColor("#FFA500"), "Alta"),
            QgsColorRampShader.ColorRampItem(3, QColor("#FF0000"), "Crítica")
        ])
    elif tipo == "ndvi":
        shader.setColorRampItemList([
            QgsColorRampShader.ColorRampItem(-1, QColor("#654321"), "Solo exposto"),
            QgsColorRampShader.ColorRampItem(0, QColor("#f5deb3"), "Pouca vegetação"),
            QgsColorRampShader.ColorRampItem(0.2, QColor("#aaffaa"), "Vegetação"),
            QgsColorRampShader.ColorRampItem(0.5, QColor("#008000"), "Vegetação densa")
        ])
    elif tipo == "temp":
        provider = layer.dataProvider()
        stats = provider.bandStatistics(1)
        min_val = stats.minimumValue
        max_val = stats.maximumValue
        shader.setColorRampItemList([
            QgsColorRampShader.ColorRampItem(min_val, QColor("#0000FF")),
            QgsColorRampShader.ColorRampItem((min_val + max_val) / 2, QColor("#FFFF00")),
            QgsColorRampShader.ColorRampItem(max_val, QColor("#FF0000"))
        ])

    raster_shader = QgsRasterShader()
    raster_shader.setRasterShaderFunction(shader)
    renderer = QgsSingleBandPseudoColorRenderer(layer.dataProvider(), 1, raster_shader)
    layer.setRenderer(renderer)
    layer.triggerRepaint()

# === CARREGAMENTO NO PROJETO ===
ndvi_layer = QgsRasterLayer(camadas[0][1], "NDVI Amparo")
temp_layer = QgsRasterLayer(camadas[1][1], "Temperatura Amparo (°C)")
ilhas_layer = QgsRasterLayer(camadas[2][1], "Ilhas de Calor - Criticidade")

QgsProject.instance().addMapLayer(ndvi_layer)
QgsProject.instance().addMapLayer(temp_layer)
QgsProject.instance().addMapLayer(ilhas_layer)

aplicar_simbologia(ndvi_layer, "ndvi")
aplicar_simbologia(temp_layer, "temp")
aplicar_simbologia(ilhas_layer, "ilhas")

print("✅ Script finalizado: NDVI, Temperatura, e Ilhas de Calor com Criticidade.")
