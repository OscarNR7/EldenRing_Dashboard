#  Elden Ring: Analizador de Metajuego y Builds

<p align="center">
  <img src="https://cdn.akamai.steamstatic.com/steam/apps/1245620/header.jpg" alt="Elden Ring Banner" width="800">
</p>

Un dashboard interactivo para el análisis de datos del universo de Elden Ring, construido con el **Stack FARM (FastAPI, React, MongoDB)**. Este proyecto aplica técnicas de ingeniería y análisis de datos para transformar un conjunto de datos crudo en una herramienta visual que revela patrones y permite optimizar builds de personajes.

---

## Descripción del Proyecto

El objetivo de este proyecto es crear una plataforma web que permita a los jugadores y analistas explorar las complejas relaciones entre clases, armas, armaduras, magias y enemigos de Elden Ring. La aplicación ingiere múltiples fuentes de datos, las procesa y las presenta en un dashboard interactivo, permitiendo responder preguntas como:

* ¿Cuál es el arma más eficiente en relación **daño/peso** para una clase específica?
* ¿Qué armaduras ofrecen la mejor **protección mágica** sin ser demasiado pesadas?
* ¿Cuáles son las **debilidades elementales** promedio de los jefes en una región?

---

## Vistazo Rápido

---

## Stack Tecnológico

Este proyecto utiliza una arquitectura de microservicios desacoplada, separando la lógica del backend, la presentación del frontend y el procesamiento de datos.

| Componente              | Tecnología                                                                                                                                                                                                                                                                                           | Propósito                                                                          |
| ----------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------- |
| **Data Pipeline** | <img src="https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white" /> <img src="https://img.shields.io/badge/Pandas-2C2D72?style=for-the-badge&logo=pandas&logoColor=white" />                                                                                        | **ETL**: Extrae, transforma y carga los datos desde los archivos CSV a MongoDB.    |
| **Base de Datos** | <img src="https://img.shields.io/badge/MongoDB-4EA94B?style=for-the-badge&logo=mongodb&logoColor=white" />                                                                                                                                                                                              | Almacenamiento NoSQL flexible para los datos semi-estructurados del juego.         |
| **Backend (API) (Futuro)** | <img src="https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi&logoColor=white" />                                                                                                                                                                                              | Sirve los datos procesados y los resultados de los análisis a través de una API REST. |
| **Frontend (Dashboard) (Futuro)**| <img src="https://img.shields.io/badge/React-20232A?style=for-the-badge&logo=react&logoColor=61DAFB" />                                                                                                                                                                                               | Interfaz de usuario interactiva para la visualización de datos y gráficos.         |

---

## 📊 Dataset Utilizado

El corazón de este proyecto son los datos, obtenidos de una fuente pública en Kaggle.

* **Nombre del Dataset**: Elden Ring Ultimate Dataset
* **Fuente**: Kaggle:
* **Enlace**: [https://www.kaggle.com/datasets/robikscube/elden-ring-ultimate-dataset](https://www.kaggle.com/datasets/robikscube/elden-ring-ultimate-dataset)
* **Descripción**: El dataset consta de **15 archivos CSV** que contienen información detallada de armas, armaduras, jefes, encantamientos, hechizos y clases, permitiendo un análisis profundo de las estadísticas y relaciones del juego.
