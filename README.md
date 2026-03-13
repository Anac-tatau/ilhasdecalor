# Automação de Ilhas de Calor Urbanas com QGIS e Python

Script em Python para execução no QGIS que automatiza o cálculo de **NDVI**, **emissividade**, **radiância**, **temperatura de superfície** e **classificação de ilhas de calor urbanas** a partir de imagens **Landsat 9**.

O projeto foi desenvolvido com foco em **reprodutibilidade**, **geotecnologias livres** e **democratização do acesso à análise climática urbana**, integrando sensoriamento remoto, processamento raster e automação em ambiente aberto.

---

## Objetivo

Desenvolver uma rotina automatizada que permita identificar e classificar áreas com diferentes níveis de criticidade térmica em ambiente urbano, reduzindo etapas manuais no QGIS e tornando o fluxo analítico mais transparente, replicável e acessível.

---

## O que o script faz

A rotina executa, de forma sequencial, as seguintes etapas:

1. Leitura das bandas Landsat 9:
   - **B4** – Red
   - **B5** – NIR
   - **B10** – Thermal

2. Cálculo do **NDVI**

3. Estimativa da **emissividade** com base no NDVI

4. Cálculo da **radiância**

5. Conversão para **temperatura de superfície**:
   - Kelvin
   - Celsius

6. Classificação das ilhas de calor urbanas em níveis de criticidade

7. Recorte dos rasters pelo limite da área de estudo

8. Aplicação de **simbologia temática automática**

9. Carregamento das camadas processadas no projeto QGIS

---

## Produtos gerados

O script gera arquivos raster intermediários e finais, como:

- `ndvi.tif`
- `emissivity.tif`
- `radiance.tif`
- `temp_kelvin.tif`
- `temp_celsius.tif`
- `ilhas_classificadas.tif`

Também podem ser geradas versões recortadas conforme o shapefile da área de estudo.

---

## Metodologia resumida

### 1. NDVI

O NDVI é calculado a partir da relação entre o infravermelho próximo e o vermelho:

\[
NDVI = \frac{NIR - RED}{NIR + RED}
\]

### 2. Emissividade

A emissividade é estimada com base na proporção de vegetação:

\[
PV = \left(\frac{NDVI - NDVI_{min}}{NDVI_{max} - NDVI_{min}}\right)^2
\]

\[
\varepsilon = 0.004 \cdot PV + 0.986
\]

### 3. Radiância

A radiância é calculada a partir da banda termal:

\[
L = (DN \cdot 0.0003342) + 0.1
\]

### 4. Temperatura de superfície

A temperatura é calculada com constantes térmicas aplicadas à banda B10 e convertida para graus Celsius.

### 5. Classificação térmica

A classificação final é feita com base na combinação entre valores de temperatura e NDVI, identificando níveis distintos de criticidade térmica.

---

## Requisitos

Para executar este script, é necessário:

- **QGIS** com suporte a Python
- Biblioteca **PyQGIS**
- Ferramentas do **GDAL**
- Módulo `processing` habilitado no QGIS
- Imagens **Landsat 9**
- Shapefile do limite da área de estudo

---

## Estrutura esperada dos dados

O script foi construído para trabalhar com:

- uma pasta contendo as bandas Landsat 9;
- um shapefile representando o recorte territorial da área de estudo.

Exemplo:

```text
/projeto
 ├── LC09_..._SR_B4.TIF
 ├── LC09_..._SR_B5.TIF
 ├── LC09_..._ST_B10.TIF
 └── limite_area_estudo.shp
