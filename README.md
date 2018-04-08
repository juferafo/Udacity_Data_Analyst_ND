# Udacity Data Analyst Nano-degree

This repository contains the projects completed and reviewed during the Udacity [Data Analyst Nano-degree](https://eu.udacity.com/course/data-analyst-nanodegree--nd002) program. For every project I provide a description of the topic and how it is organized.

## Projects

###  I) Intro to Data Analysis: Investigate a Dataset 

### II) Data Wrangling: Wrangle OpenStreetMap Data

In this project, I wrangled a large XML Open Street Map database (OSM). Due to the human entered data of the source, I employed data munging techniques to ensure the quality of it. I wrote python routines to check the validity, consistency and uniformity of some target fields. After cleaning, the OSM was transformed into a database that was queried (SQL) to get information about its content.

#### Contents

The content of this work is stored into ```./Wrangle_OpenStreetMap_Data```, where the ```process_data.py``` file is the main script. It reads, cleans and converts the OSM in a database by importing the methods coded in ```clean.py``` and ```create_db.py```. One can also find the different branches of the OSM in the corresponding ```csv``` files. The review of this project can be found in ```Data_Wrangling_Project.html``` or in the ```Data_Wrangling_Project.ipynb``` jupyter notebook.
