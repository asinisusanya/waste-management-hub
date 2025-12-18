# Waste Processing Facility Location Optimizer

[![Streamlit App](https://img.shields.io/badge/Streamlit-App-brightgreen)](https://streamlit.io)
[![Python](https://img.shields.io/badge/Python-3.8%2B-blue)](https://python.org)


## 🚀 Overview

Advanced optimization model using **L-BFGS-B** algorithm to find optimal waste processing facility locations serving Sri Lanka's **Board of Investment (BOI) zones**. Integrates **GIS constraints** (protected areas, water bodies, sensitive sites) with transportation cost minimization.

## ✨ Features

- **Geospatial Constraints**: Exclusion zones, buffer distances, country boundaries
- **Interactive Streamlit App**: Easy input, instant results, map visualization
- **Scalable Optimization**: Handles multiple waste zones efficiently
- **Real-time Scenario Analysis**: Test different configurations instantly

## 🛠️ Tech Stack
Python | GeoPandas | Shapely | SciPy | Streamlit | Matplotlib | NumPy

## 🎯 How It Works

1. **Input**: BOI zone coordinates & waste quantities
2. **Constraints**: Exclusion zones + buffer distances
3. **Optimization**: L-BFGS-B minimizes transport costs
4. **Output**: Optimal facility location on interactive map

## 📊 Results

**Optimal Location**: Found within seconds considering all real-world constraints
**Visualization**: Clear map showing BOI zones, exclusions, and best site

## 🔬 Novelty

- Combines advanced optimization with practical GIS constraints
- User-friendly interface for non-technical planners
- Sri Lanka-specific waste management solution






